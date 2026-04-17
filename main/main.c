#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

void app_main(void){
    printf("teste\n");
    vTaskDelay(pdMS_TO_TICKS(500));
}