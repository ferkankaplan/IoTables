/*
  IoTables Table Display Firmware

  Generated file target:
  - One file per table, for example masa000.ino, masa001.ino.
  - The backend must generate WIFI_SSID, WIFI_PASSWORD, DISPLAY_CREDENTIAL,
    TENANT_HOST, TABLE_LABEL, and IOTABLES_ROOT_CA per table creation result.

  Arduino libraries:
  - TFT_eSPI
  - QRCode

  TFT_eSPI must be configured for the exact ESP32/TFT board in its User_Setup.h
  or project-specific setup file. This sketch owns IoTables behavior; display
  pin mapping belongs to the board profile.
*/

#include <HTTPClient.h>
#include <QRCode.h>
#include <TFT_eSPI.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <string.h>

// ---------------------------------------------------------------------------
// Generated per-table configuration.
// ---------------------------------------------------------------------------

static const char* WIFI_SSID = "__IOTABLES_WIFI_SSID__";
static const char* WIFI_PASSWORD = "__IOTABLES_WIFI_PASSWORD__";

static const char* TENANT_HOST = "__IOTABLES_TENANT_HOST__";
static const char* TABLE_LABEL = "__IOTABLES_TABLE_LABEL__";

// This is a table-display credential, not a customer QR token. It must never
// be shown on screen or embedded into the QR payload.
static const char* DISPLAY_CREDENTIAL = "__IOTABLES_DISPLAY_CREDENTIAL__";

// Generator must inject the root CA used by the tenant HTTPS endpoint.
static const char IOTABLES_ROOT_CA[] PROGMEM = R"EOF(__IOTABLES_TLS_ROOT_CA_PEM__)EOF";

// Use the staging or production tenant host. The firmware always calls the
// same-origin API path for the tenant namespace.
static const char* QR_ENDPOINT_PATH = "/api/table-display/qr-token";

// ---------------------------------------------------------------------------
// Runtime tuning.
// ---------------------------------------------------------------------------

static const uint32_t WIFI_CONNECT_TIMEOUT_MS = 20000;
static const uint32_t HTTP_TIMEOUT_MS = 10000;
static const uint32_t MIN_REFRESH_INTERVAL_MS = 5000;
static const uint32_t RETRY_INTERVAL_MS = 5000;
static const uint32_t CLOCK_TEXT_REFRESH_MS = 1000;

static const uint16_t COLOR_BACKGROUND = TFT_BLACK;
static const uint16_t COLOR_FOREGROUND = TFT_WHITE;
static const uint16_t COLOR_MUTED = TFT_DARKGREY;
static const uint16_t COLOR_ERROR = TFT_RED;

TFT_eSPI tft = TFT_eSPI();
static uint8_t qrcodeData[3917];

struct QrPayload {
  String token;
  uint32_t refreshAfterSeconds;
  bool ok;
};

bool configurationIsComplete();
bool isPlaceholder(const char* value);
void configureTls(WiFiClientSecure& client);
void connectWifi();
QrPayload fetchQrPayload();
void drawQr(const String& token);
uint8_t selectQrVersion(size_t length);
void drawCountdown();
void drawStatus(const char* title, const char* subtitle);
String extractJsonString(const String& json, const char* key);
uint32_t extractJsonUInt(const String& json, const char* key, uint32_t fallback);
bool timeReached(uint32_t now, uint32_t target);

String currentToken = "";
uint32_t nextRefreshAtMs = 0;
uint32_t tokenExpiresAtMs = 0;
uint32_t lastClockPaintMs = 0;
bool screenHasQr = false;
bool configurationReady = false;

void setup() {
  Serial.begin(115200);
  delay(200);

  tft.init();
  tft.setRotation(1);
  tft.fillScreen(COLOR_BACKGROUND);
  tft.setTextColor(COLOR_FOREGROUND, COLOR_BACKGROUND);
  tft.setTextDatum(MC_DATUM);

  configurationReady = configurationIsComplete();
  if (!configurationReady) {
    drawStatus("Eksik kurulum", "Firmware tekrar uretilmeli.");
    return;
  }

  drawStatus("IoTables", "WiFi baglaniyor...");
  connectWifi();
}

void loop() {
  if (!configurationReady) {
    delay(1000);
    return;
  }

  if (WiFi.status() != WL_CONNECTED) {
    screenHasQr = false;
    drawStatus("Baglanti yok", "WiFi tekrar deneniyor...");
    connectWifi();
    delay(RETRY_INTERVAL_MS);
    return;
  }

  const uint32_t now = millis();
  if (currentToken.length() == 0 || timeReached(now, nextRefreshAtMs)) {
    QrPayload payload = fetchQrPayload();
    if (payload.ok) {
      currentToken = payload.token;
      const uint32_t ttlMs = payload.refreshAfterSeconds * 1000UL;
      const uint32_t refreshMs = ttlMs > 2000 ? ttlMs - 1000 : ttlMs;
      tokenExpiresAtMs = now + ttlMs;
      nextRefreshAtMs = now + max(refreshMs, MIN_REFRESH_INTERVAL_MS);
      drawQr(currentToken);
      screenHasQr = true;
    } else {
      screenHasQr = false;
      currentToken = "";
      nextRefreshAtMs = now + RETRY_INTERVAL_MS;
      drawStatus("QR alinamadi", "Sunucu tekrar denenecek.");
    }
  }

  if (screenHasQr && timeReached(now, lastClockPaintMs + CLOCK_TEXT_REFRESH_MS)) {
    drawCountdown();
    lastClockPaintMs = now;
  }

  delay(100);
}

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  const uint32_t startedAt = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
    if (millis() - startedAt > WIFI_CONNECT_TIMEOUT_MS) {
      Serial.println();
      Serial.println("WiFi connect timeout");
      WiFi.disconnect(true);
      delay(500);
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
      break;
    }
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.print("WiFi connected: ");
    Serial.println(WiFi.localIP());
    drawStatus("Baglandi", "QR hazirlaniyor...");
  }
}

QrPayload fetchQrPayload() {
  QrPayload payload;
  payload.ok = false;
  payload.refreshAfterSeconds = 60;

  WiFiClientSecure client;
  configureTls(client);

  HTTPClient http;
  String url = String("https://") + TENANT_HOST + QR_ENDPOINT_PATH;
  if (!http.begin(client, url)) {
    Serial.println("HTTP begin failed");
    return payload;
  }

  http.setTimeout(HTTP_TIMEOUT_MS);
  http.addHeader("Authorization", String("DisplayCredential ") + DISPLAY_CREDENTIAL);

  const int statusCode = http.GET();
  const String body = http.getString();
  http.end();

  Serial.print("QR fetch status: ");
  Serial.println(statusCode);

  if (statusCode != 200) {
    Serial.println(body);
    return payload;
  }

  String qrToken = extractJsonString(body, "qrToken");
  uint32_t refreshAfterSeconds = extractJsonUInt(body, "refreshAfterSeconds", 60);

  if (qrToken.length() == 0) {
    Serial.println("qrToken missing");
    return payload;
  }

  payload.token = qrToken;
  payload.refreshAfterSeconds = refreshAfterSeconds;
  payload.ok = true;
  return payload;
}

void drawQr(const String& token) {
  tft.fillScreen(COLOR_BACKGROUND);

  const int16_t width = tft.width();
  const int16_t height = tft.height();
  const int16_t headerHeight = 34;
  const int16_t footerHeight = 28;
  const int16_t qrArea = min(width, height - headerHeight - footerHeight) - 12;
  const int16_t qrX = (width - qrArea) / 2;
  const int16_t qrY = headerHeight + 4;

  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(COLOR_FOREGROUND, COLOR_BACKGROUND);
  tft.drawString(TABLE_LABEL, width / 2, 8, 2);

  QRCode qrcode;
  const uint8_t qrVersion = selectQrVersion(token.length());
  const uint16_t bufferSize = qrcode_getBufferSize(qrVersion);

  if (bufferSize > sizeof(qrcodeData)) {
    drawStatus("QR buyuk", "Token cizilemedi.");
    return;
  }

  qrcode_initText(&qrcode, qrcodeData, qrVersion, ECC_LOW, token.c_str());

  const int moduleCount = qrcode.size;
  const int scale = max(1, qrArea / moduleCount);
  const int renderedSize = moduleCount * scale;
  const int offsetX = qrX + (qrArea - renderedSize) / 2;
  const int offsetY = qrY + (qrArea - renderedSize) / 2;

  tft.fillRect(offsetX - 4, offsetY - 4, renderedSize + 8, renderedSize + 8, COLOR_FOREGROUND);

  for (uint8_t y = 0; y < moduleCount; y++) {
    for (uint8_t x = 0; x < moduleCount; x++) {
      const uint16_t color = qrcode_getModule(&qrcode, x, y) ? TFT_BLACK : COLOR_FOREGROUND;
      tft.fillRect(offsetX + x * scale, offsetY + y * scale, scale, scale, color);
    }
  }

  drawCountdown();
}

uint8_t selectQrVersion(size_t length) {
  if (length <= 84) {
    return 5;
  }
  if (length <= 122) {
    return 7;
  }
  if (length <= 180) {
    return 9;
  }
  return 12;
}

void drawCountdown() {
  const int16_t y = tft.height() - 22;
  tft.fillRect(0, y - 2, tft.width(), 24, COLOR_BACKGROUND);

  uint32_t remainingSeconds = 0;
  if (!timeReached(millis(), tokenExpiresAtMs)) {
    remainingSeconds = (tokenExpiresAtMs - millis()) / 1000UL;
  }

  tft.setTextDatum(BC_DATUM);
  tft.setTextColor(COLOR_MUTED, COLOR_BACKGROUND);
  tft.drawString(String("Yenilenme: ") + remainingSeconds + " sn", tft.width() / 2, tft.height() - 4, 2);
}

void drawStatus(const char* title, const char* subtitle) {
  tft.fillScreen(COLOR_BACKGROUND);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(COLOR_FOREGROUND, COLOR_BACKGROUND);
  tft.drawString(title, tft.width() / 2, (tft.height() / 2) - 16, 2);
  tft.setTextColor(COLOR_MUTED, COLOR_BACKGROUND);
  tft.drawString(subtitle, tft.width() / 2, (tft.height() / 2) + 14, 2);
}

String extractJsonString(const String& json, const char* key) {
  const String pattern = String("\"") + key + "\":";
  int keyIndex = json.indexOf(pattern);
  if (keyIndex < 0) {
    return "";
  }

  int valueStart = json.indexOf('"', keyIndex + pattern.length());
  if (valueStart < 0) {
    return "";
  }
  valueStart++;

  String value = "";
  bool escaped = false;
  for (int i = valueStart; i < json.length(); i++) {
    const char c = json.charAt(i);
    if (escaped) {
      value += c;
      escaped = false;
      continue;
    }
    if (c == '\\') {
      escaped = true;
      continue;
    }
    if (c == '"') {
      return value;
    }
    value += c;
  }
  return "";
}

uint32_t extractJsonUInt(const String& json, const char* key, uint32_t fallback) {
  const String pattern = String("\"") + key + "\":";
  int keyIndex = json.indexOf(pattern);
  if (keyIndex < 0) {
    return fallback;
  }

  int valueStart = keyIndex + pattern.length();
  while (valueStart < json.length() && json.charAt(valueStart) == ' ') {
    valueStart++;
  }

  uint32_t value = 0;
  bool hasDigit = false;
  for (int i = valueStart; i < json.length(); i++) {
    const char c = json.charAt(i);
    if (c < '0' || c > '9') {
      break;
    }
    hasDigit = true;
    value = value * 10 + static_cast<uint32_t>(c - '0');
  }

  return hasDigit ? value : fallback;
}

bool timeReached(uint32_t now, uint32_t target) {
  return static_cast<int32_t>(now - target) >= 0;
}

bool configurationIsComplete() {
  if (isPlaceholder(WIFI_SSID) || isPlaceholder(WIFI_PASSWORD)) {
    Serial.println("WiFi configuration placeholder is not replaced");
    return false;
  }
  if (isPlaceholder(TENANT_HOST) || isPlaceholder(TABLE_LABEL)) {
    Serial.println("Tenant/table placeholder is not replaced");
    return false;
  }
  if (isPlaceholder(DISPLAY_CREDENTIAL)) {
    Serial.println("Display credential placeholder is not replaced");
    return false;
  }
  if (isPlaceholder(IOTABLES_ROOT_CA)) {
    Serial.println("TLS root CA placeholder is not replaced");
    return false;
  }
  return true;
}

bool isPlaceholder(const char* value) {
  if (value == nullptr || value[0] == '\0') {
    return true;
  }
  return strstr(value, "__IOTABLES_") != nullptr;
}

void configureTls(WiFiClientSecure& client) {
  client.setCACert(IOTABLES_ROOT_CA);
}
