#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <DHT20.h>

// Thông tin kết nối
const char *ssid = "ACLAB";
const char *password = "ACLAB2023";
// --- Thông tin Azure IoT Hub của bạn ---
const char *mqtt_server = "";
const char *device_id = "esp32-id1";

const char *mqtt_user = "";

const char *mqtt_pass = "";

const char *mqtt_topic = "devices/esp32-id1/messages/events/";

WiFiClientSecure espClient;
PubSubClient client(espClient);
DHT20 dht;

void setup()
{
    Serial.begin(115200);
    dht.begin();
    Wire.begin(11, 12);
    // Kết nối WiFi
    WiFi.begin(ssid, password);
    // ... đợi kết nối ...

    // Azure yêu cầu TLS
    espClient.setInsecure(); // Để test nhanh, hoặc dùng setCACert nếu chạy thực tế

    client.setServer(mqtt_server, 8883);
}

void loop()
{
    if (!client.connected())
    {
        if (client.connect(device_id, mqtt_user, mqtt_pass))
        {
            Serial.println("Connected to Azure!");
        }
    }

    dht.read();
    float temp = dht.getTemperature();

    String payload = "{\"temp\":" + String(dht.getTemperature()) + "}\n";
    client.publish(mqtt_topic, payload.c_str());
    Serial.print(payload);

    delay(10000);
}