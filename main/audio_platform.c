#include "audio_interface.h"
#include "esp_log.h"

void audio_listener_task(void *pvParameters){
    AudioProcessor_t *processor = (AudioProcessor_t *) pvParameters;
    int16_t pcm_buffer[SAMPLES_PER_WINDOW];

    ESP_LOGI("AUDIO PLATFORM", "Modulo de Escrita iniciado. Aguardando stream...");

    while(1) {
        size_t bytes_read = xStreamBufferReceive(
            processor->input_stream,
            (void *) pcm_buffer,
            sizeof(pcm_buffer),
            portMAX_DELAY
        );

        if(bytes_read > 0 && processor->on_data_received != NULL) {
            processor->on_data_received(pcm_buffer, bytes_read / sizeof(int16_t));
        }
    }
}