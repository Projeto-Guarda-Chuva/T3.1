#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/stream_buffer.h"
#include <math.h>
#include "esp_log.h"
#include "esp_dsp.h"

#include "audio_interface.h"

#define N_SAMPLES 256

/*
Arrays globais/estáticos para não estourar a stack da Task
A FFT do ESP-DSP precisa que os dados de entrada tenham o dobro do tamanho (Real + Imaginário)
*/
__attribute__((aligned(16))) float y_cf[N_SAMPLES * 2]; 
__attribute__((aligned(16))) float window[N_SAMPLES];


void init_dsp() {
    esp_err_t ret = dsps_fft2r_init_fc32(NULL, CONFIG_DSP_MAX_FFT_SIZE);
    if (ret == ESP_OK) {
        ESP_LOGI("DSP", "FFT inicializada com sucesso!");
    }

    // Gera a janela de Hann (reduz vazamento espectral nas pontas da amostra)
    dsps_wind_hann_f32(window, N_SAMPLES); 
}

void minha_funcao_de_analise(const int16_t* data, size_t size) {
    if (size < N_SAMPLES) return;

    // Converter int16_t para float e aplicar a janela (Windowing)
    for (int i = 0; i < N_SAMPLES; i++) {
        y_cf[i * 2] = (float)data[i] * window[i];
        y_cf[i * 2 + 1] = 0.0f;                   
    }

    // Executar a FFT complexa
    dsps_fft2r_fc32(y_cf, N_SAMPLES);
    
    // Reverter a ordem dos bits
    dsps_bit_rev_fc32(y_cf, N_SAMPLES);
    
    // Calcular a Magnitude
    for (int i = 0; i < N_SAMPLES / 2; i++) {
        float power = (y_cf[i * 2] * y_cf[i * 2] + y_cf[i * 2 + 1] * y_cf[i * 2 + 1]) / N_SAMPLES;
        if (power < 1e-10f) power = 1e-10f; // Evitar log de zero
        y_cf[i] = 10 * log10f(power);
    }

    // Imprime um cabeçalho para facilitar a exportação para CSV
    ESP_LOGI("AUDIO_DSP_CSV", "--- INICIO DOS DADOS ---");
    ESP_LOGI("AUDIO_DSP_CSV", "Frequencia (Hz), Amplitude (dB)");

    // Iterar sobre todos os bins de frequência (até N_SAMPLES/2 - frequência de Nyquist)
    for (int i = 0; i < N_SAMPLES / 2; i++) {
        float bin_frequency = (i * (float)AUDIO_SAMPLE_RATE) / N_SAMPLES;
        
        // Pegando os valores absolutos da amplitude
        if(y_cf[i] < 0)
            y_cf[i] = y_cf[i] * -1;

        ESP_LOGI("AUDIO_DSP_CSV", "%.2f, %.2f", bin_frequency, y_cf[i]);

    }
    ESP_LOGI("AUDIO_DSP_CSV", "--- FIM DOS DADOS ---");
    vTaskDelay(pdMS_TO_TICKS(100));
}

void app_main() {
    ESP_LOGI("MAIN_APP", "Iniciando plataforme de audio ESP32-P4");

    init_dsp();

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
    meu_processador.on_data_received = minha_funcao_de_analise;

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