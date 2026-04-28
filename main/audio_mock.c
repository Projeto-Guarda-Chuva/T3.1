#include "audio_interface.h"
#include "freertos/task.h"
#include "esp_log.h"

void audio_mock_capture_task(void *pvParameters) {
    StreamBufferHandle_t stream = (StreamBufferHandle_t) pvParameters;
    int16_t mock_data[SAMPLES_PER_WINDOW];
    TickType_t xLastWakeTime = xTaskGetTickCount();

    while(1) {
        // Simula a entrada de dados
        for(int i = 0; i < SAMPLES_PER_WINDOW; i++){
            mock_data[i] = (int16_t)(rand() % 2000 - 1000);
        }

        xStreamBufferSend(stream, (void*)mock_data, sizeof(mock_data), 0);

        vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(AUDIO_WIDOW_MS));
    }
}