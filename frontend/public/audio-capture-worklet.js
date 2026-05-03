/* global AudioWorkletProcessor, registerProcessor */

class AudioCaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.targetSampleRate = 16000;
    this.sourceSampleRate = sampleRate;
    this.resampleRatio = this.sourceSampleRate / this.targetSampleRate;
    this.resampleInputOffset = 0;

    // Buffer size of 4096 samples (256ms at 16kHz) to avoid sending too many small packets
    this.bufferSize = 4096;
    this.buffer = new Int16Array(this.bufferSize);
    this.frameCount = 0;

    this.port.onmessage = (event) => {
      if (event.data?.type === "flush") {
        this.flush();
      }
    };
  }

  appendSample(floatSample) {
    const sample = Math.max(-1, Math.min(1, floatSample));
    this.buffer[this.frameCount] = sample < 0 ? sample * 32768 : sample * 32767;
    this.frameCount++;

    if (this.frameCount >= this.bufferSize) {
      this.sendFullBuffer();
    }
  }

  sendFullBuffer() {
    const sendBuffer = new Int16Array(this.buffer);
    this.port.postMessage(sendBuffer.buffer, [sendBuffer.buffer]);
    this.frameCount = 0;
  }

  flush() {
    if (this.frameCount <= 0) {
      return;
    }

    const sendBuffer = this.buffer.slice(0, this.frameCount);
    this.port.postMessage(sendBuffer.buffer, [sendBuffer.buffer]);
    this.frameCount = 0;
  }

  processInputAtNativeRate(channelData) {
    for (let index = 0; index < channelData.length; index++) {
      this.appendSample(channelData[index]);
    }
  }

  processInputAtTargetRate(channelData) {
    let sourceIndex = this.resampleInputOffset;
    const lastIndex = channelData.length - 1;

    while (sourceIndex < lastIndex) {
      const left = Math.floor(sourceIndex);
      const right = Math.min(left + 1, lastIndex);
      const interpolation = sourceIndex - left;
      this.appendSample(channelData[left] + (channelData[right] - channelData[left]) * interpolation);
      sourceIndex += this.resampleRatio;
    }

    this.resampleInputOffset = sourceIndex - channelData.length;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || !input[0]) return true;

    const channelData = input[0];

    if (this.sourceSampleRate === this.targetSampleRate) {
      this.processInputAtNativeRate(channelData);
    } else {
      this.processInputAtTargetRate(channelData);
    }

    return true; // Keep the processor alive
  }
}

registerProcessor("audio-capture-processor", AudioCaptureProcessor);
