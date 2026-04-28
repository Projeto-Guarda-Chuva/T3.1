#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/stream_buffer.h"
#include "esp_log.h"

#include "audio_interface.h"

void funcao_teste(const int16_t *data, size_t size){
    // Aplicar aqui os algorimtos de processamento de audio
    for(int i = 0; i < 10; i++){
        printf("%d ", data[i]);
    }
    printf("\n");
    ESP_LOGI("MAIN_APP", "processando bloco de %d samples", size);
    vTaskDelay(pdMS_TO_TICKS(100));
}

void app_main() {
    ESP_LOGI("MAIN_APP", "Iniciando plataforme de audio ESP32-P4");

    StreamBufferHandle_t audio_stream = xStreamBufferCreate(
        AUDIO_BUFFER_SIZE_BYTES * 5,
        AUDIO_BUFFER_SIZE_BYTES
    );

    if(audio_stream == NULL){
        ESP_LOGE("MAIN_APP", "falha ao criar o Stream Buffer");
        return;
    }

    static AudioProcessor_t meu_processador;
    meu_processador.input_stream = audio_stream;
    meu_processador.on_data_received = funcao_teste;

    xTaskCreate(
        audio_listener_task,
        "audio_listener",
        4096,
        &meu_processador,
        10,
        NULL
    );

    xTaskCreate(
        audio_mock_capture_task,
        "audio_modck",
        4096,
        (void*)audio_stream,
        5, 
        NULL
    );

    return;
}