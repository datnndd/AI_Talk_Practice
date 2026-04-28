const encodeWav = ({ samples, sampleRate }) => {
  const dataLength = samples.length * 2;
  const buffer = new ArrayBuffer(44 + dataLength);
  const view = new DataView(buffer);

  const writeString = (offset, value) => {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + dataLength, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, dataLength, true);

  let offset = 44;
  for (let index = 0; index < samples.length; index += 1, offset += 2) {
    const sample = Math.max(-1, Math.min(1, samples[index]));
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
  }

  return new Blob([buffer], { type: "audio/wav" });
};

const mergeBuffers = (chunks, length) => {
  const samples = new Float32Array(length);
  let offset = 0;
  chunks.forEach((chunk) => {
    samples.set(chunk, offset);
    offset += chunk.length;
  });
  return samples;
};

export const blobToBase64 = (blob) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });

export const createRecorder = async ({ onStop }) => {
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  const audioContext = new AudioContextClass();
  const source = audioContext.createMediaStreamSource(stream);
  const processor = audioContext.createScriptProcessor(4096, 1, 1);
  const chunks = [];
  let totalLength = 0;
  let isRecording = false;
  let isStopped = false;

  processor.onaudioprocess = (event) => {
    if (!isRecording || isStopped) {
      return;
    }
    const input = event.inputBuffer.getChannelData(0);
    chunks.push(new Float32Array(input));
    totalLength += input.length;
  };

  source.connect(processor);
  processor.connect(audioContext.destination);

  const cleanup = async () => {
    source.disconnect();
    processor.disconnect();
    stream.getTracks().forEach((track) => track.stop());
    await audioContext.close();
  };

  return {
    start: () => {
      isRecording = true;
    },
    stop: async () => {
      if (isStopped) {
        return;
      }
      isStopped = true;
      isRecording = false;
      const samples = mergeBuffers(chunks, totalLength);
      const blob = encodeWav({ samples, sampleRate: audioContext.sampleRate });
      await cleanup();
      onStop(await blobToBase64(blob));
    },
  };
};
