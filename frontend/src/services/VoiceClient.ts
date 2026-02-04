export class VoiceClient {
    private mediaRecorder: MediaRecorder | null = null;
    private audioChunks: Blob[] = [];

    async startRecording(): Promise<void> {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Media Devices API not supported');
        }

        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.mediaRecorder = new MediaRecorder(stream);
        this.audioChunks = [];

        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.audioChunks.push(event.data);
            }
        };

        this.mediaRecorder.start();
    }

    stopRecording(): Promise<Blob> {
        return new Promise((resolve, reject) => {
            if (!this.mediaRecorder) {
                reject(new Error('Recorder not initialized'));
                return;
            }

            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                this.audioChunks = [];

                // Stop all tracks to release microphone
                this.mediaRecorder?.stream.getTracks().forEach(track => track.stop());
                this.mediaRecorder = null;

                resolve(audioBlob);
            };

            this.mediaRecorder.stop();
        });
    }
}

export const voiceClient = new VoiceClient();
