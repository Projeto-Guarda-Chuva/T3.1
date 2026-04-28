#ifndef AUDIO_INTERFACE_H
#define AUDIO_INTERFACE_H

#include "freertos/FreeRTOS.h"
#include "freertos/stream_buffer.h"


#define AUDIO_SAMPLE_RATE 16000 // 16kHz
#define AUDIO_BITS_PER_SAMPLE 16
#define AUDIO_CHANNELS 1 // audio monofônico
#define AUDIO_WIDOW_MS 20 
#define SAMPLES_PER_WINDOW ((AUDIO_SAMPLE_RATE * AUDIO_WIDOW_MS) / 1000)
#define AUDIO_BUFFER_SIZE_BYTES (SAMPLES_PER_WINDOW * (AUDIO_BITS_PER_SAMPLE / 8) * AUDIO_CHANNELS)

typedef struct {
    StreamBufferHandle_t input_stream;
    void (*on_data_received)(const int16_t* data, size_t size); // callback
} AudioProcessor_t;

void audio_listener_task(void *pvParameters);
void audio_mock_capture_task(void *pvParameters);

#endif // AUDIO_INTERFACE_H