#pragma once


namespace GPIOController {
    void init(void(*button_press_callback)());
    void tick();
    void configure_no_wifi();
    void configure_idle_flash();
    void configure_alarm();
};