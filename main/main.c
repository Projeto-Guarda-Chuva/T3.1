#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/ringbuf.h"

RingbufHandle_t audio_ring_buffer;

// Task que finge ser a camada de Captura de Áudio
void mock_capture_task(void *params) {
    while (1) {
        // Simula a captura de 512 bytes de áudio com ruído aleatório
        int16_t fake_buffer[256]; 
        for(int i=0; i<256; i++) fake_buffer[i] = rand() % 100; 

        xRingbufferSend(audio_ring_buffer, fake_buffer, sizeof(fake_buffer), pdMS_TO_TICKS(100));
        
        // Simula o tempo de preenchimento do buffer (tempo real)
        vTaskDelay(pdMS_TO_TICKS(20)); 
    }
}

// Task de Processador de audio
void audio_processor_task(void *params) {
    size_t item_size;
    while (1) {
        // Fica bloqueado até receber dados do Ring Buffer
        int16_t *item = (int16_t *)xRingbufferReceive(audio_ring_buffer, &item_size, portMAX_DELAY);
        int number__bytes_element = 2;
        if (item != NULL) {
            // Exemplo calcular "Volume" simples
            int32_t sum = 0;
            for (int i = 0; i < (item_size / number__bytes_element); i++) {
                sum += abs(item[i]);
            }
            int avg_volume = sum / (item_size / number__bytes_element);

            printf("Processador: Volume médio detectado: %d\n", avg_volume);
            vTaskDelay(1000 / portTICK_PERIOD_MS);
            // Aqui você enviaria o resultado para a próxima camada...

            vRingbufferReturnItem(audio_ring_buffer, (void *)item);
        }
    }
}

void app_main() {
    // Cria o Ring Buffer de 8KB
    audio_ring_buffer = xRingbufferCreate(8192, RINGBUF_TYPE_NOSPLIT);

    xTaskCreate(mock_capture_task, "Capture", 2048, NULL, 5, NULL);
    xTaskCreate(audio_processor_task, "Processor", 4096, NULL, 5, NULL);
}