export function createConversationWebSocketUrl(apiBaseUrl) {
  const httpBase = (apiBaseUrl || window.location.origin).replace(/\/api\/?$/, "");
  return `${httpBase.replace(/^http/, "ws")}/ws/conversation`;
}

export function resampleFloat32(input, inputSampleRate, targetSampleRate) {
  if (inputSampleRate === targetSampleRate) {
    return new Float32Array(input);
  }

  const sampleCount = Math.max(1, Math.round(input.length * targetSampleRate / inputSampleRate));
  const output = new Float32Array(sampleCount);
  const ratio = inputSampleRate / targetSampleRate;

  for (let index = 0; index < sampleCount; index += 1) {
    const sourceIndex = index * ratio;
    const left = Math.floor(sourceIndex);
    const right = Math.min(left + 1, input.length - 1);
    const interpolation = sourceIndex - left;
    output[index] = input[left] + (input[right] - input[left]) * interpolation;
  }

  return output;
}

export function float32ToPcm16(input) {
  const pcm = new Int16Array(input.length);

  for (let index = 0; index < input.length; index += 1) {
    const sample = Math.max(-1, Math.min(1, input[index]));
    pcm[index] = sample < 0 ? sample * 32768 : sample * 32767;
  }

  return pcm;
}

export function pcm16ToFloat32(buffer) {
  const pcm = new Int16Array(buffer);
  const float32 = new Float32Array(pcm.length);

  for (let index = 0; index < pcm.length; index += 1) {
    float32[index] = pcm[index] / 32768;
  }

  return float32;
}

export function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";

  for (let index = 0; index < bytes.length; index += 1) {
    binary += String.fromCharCode(bytes[index]);
  }

  return window.btoa(binary);
}

export function base64ToArrayBuffer(base64) {
  const binary = window.atob(base64);
  const bytes = new Uint8Array(binary.length);

  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }

  return bytes.buffer;
}

export function formatDuration(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}
