#include "audio_interface.h"
#include "freertos/task.h"
#include "esp_log.h"
#include <math.h>

static const char *TAG = "AUDIO_MOCK";

// Numero de senoides vão compor o nosso sinal
#define NUM_SINES 3

void audio_mock_capture_task(void *pvParameters) {
    StreamBufferHandle_t stream = (StreamBufferHandle_t)pvParameters;
    int16_t mock_data[SAMPLES_PER_WINDOW];
    TickType_t xLastWakeTime = xTaskGetTickCount();

    //Configuração dos parâmetros de cada senoide
    const float frequencies[NUM_SINES] = {500.0f, 1500.0f, 3500.0f};
    
    // A soma das amplitudes (12000 + 8000 + 6000 = 26000) deve ser menor que 32767
    const float amplitudes[NUM_SINES]  = {12000.0f, 8000.0f, 6000.0f};
    
    // Arrays para manter o estado da fase de cada onda
    float phases[NUM_SINES] = {0.0f, 0.0f, 0.0f};
    float phase_increments[NUM_SINES];

    // Pré-cálculo dos incrementos de fase (ganho de performance)
    for (int j = 0; j < NUM_SINES; j++) {
        phase_increments[j] = 2.0f * M_PI * frequencies[j] / AUDIO_SAMPLE_RATE;
    }

    ESP_LOGI(TAG, "Gerador de Sinal Composto Iniciado.");

    while (1) {
        // Geração do sinal complexo contínuo
        for (int i = 0; i < SAMPLES_PER_WINDOW; i++) {
            float sample_val = 0.0f;

            // Soma a contribuição de cada uma das senoides para o instante atual
            for (int j = 0; j < NUM_SINES; j++) {
                sample_val += amplitudes[j] * sin(phases[j]);
                phases[j] += phase_increments[j];
                
                // Mantém a fase num limite seguro para evitar overflow da variável float
                if (phases[j] >= 2.0f * M_PI) {
                    phases[j] -= 2.0f * M_PI;
                }
            }

            mock_data[i] = (int16_t)sample_val;
        }

        // Envia o bloco de áudio gerado para a camada superior
        xStreamBufferSend(stream, (void *)mock_data, sizeof(mock_data), 0);
        
        vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(AUDIO_WINDOW_MS));
    }
}