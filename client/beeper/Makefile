# -------- Config --------
FQBN        := rp2040:rp2040:rpipicow
PORT        := COM4
SKETCH_DIR  := .

# -------- Commands --------
ARDUINO     := arduino-cli

# -------- Targets --------
.PHONY: all build upload flash clean find debug

all: build

build:
	$(ARDUINO) compile --fqbn $(FQBN) $(SKETCH_DIR)

upload:
	$(ARDUINO) upload -p $(PORT) --fqbn $(FQBN) $(SKETCH_DIR)

flash: build upload

clean:
	$(ARDUINO) cache clean

find:
	$(ARDUINO) board list

debug:
	$(ARDUINO) monitor -p $(PORT) -c 115200

