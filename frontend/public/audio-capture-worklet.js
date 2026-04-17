/* global AudioWorkletProcessor, registerProcessor */

class AudioCaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    // Buffer size of 4096 samples (256ms at 16kHz) to avoid sending too many small packets
    this.bufferSize = 4096;
    this.buffer = new Int16Array(this.bufferSize);
    this.frameCount = 0;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || !input[0]) return true;

    const channelData = input[0];

    // Convert float32 bounds [-1.0, 1.0] to int16
    for (let i = 0; i < channelData.length; i++) {
        const sample = Math.max(-1, Math.min(1, channelData[i]));
        this.buffer[this.frameCount] = sample < 0 ? sample * 32768 : sample * 32767;
        this.frameCount++;

        if (this.frameCount >= this.bufferSize) {
             // Create a copy to transfer back to the main thread
             const sendBuffer = new Int16Array(this.buffer);
             // Transfer the buffer natively across threads to prevent allocation overhead
             this.port.postMessage(sendBuffer.buffer, [sendBuffer.buffer]);
             this.frameCount = 0;
        }
    }

    return true; // Keep the processor alive
  }
}

registerProcessor("audio-capture-processor", AudioCaptureProcessor);
