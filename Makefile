PROJECT ?= guidage_robot
PROJECT_DIR := $(PROJECT)
FIRMWARE := $(PROJECT_DIR)/firmware.py
CONTROLLER := $(PROJECT_DIR)/telecommande.py

PYTHON := .venv/bin/python
UFLASH := .venv/bin/uflash
UFS := .venv/bin/ufs
SERIAL_PORT := $(firstword $(wildcard /dev/cu.usbmodem*))

.PHONY: help setup check check-controller flash install run start stop reset status serial

help:
	@echo "Projet selectionne : $(PROJECT)"
	@echo "make setup                    Cree l'environnement Python"
	@echo "make flash                    Flashe le firmware sur la micro:bit"
	@echo "make install                  Installe le firmware via le port serie"
	@echo "make run                      Lance la telecommande si disponible"
	@echo "make serial                   Ouvre la console serie"
	@echo "make run PROJECT=autre_projet Lance un autre projet"

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install uflash microfs

check:
	@test -x "$(PYTHON)" || { echo "Erreur : lancez 'make setup'."; exit 1; }
	@test -f "$(FIRMWARE)" || { echo "Erreur : firmware introuvable : $(FIRMWARE)"; exit 1; }
	PYTHONPYCACHEPREFIX=/tmp/robotique-pycache $(PYTHON) -m py_compile "$(FIRMWARE)"

check-controller: check
	@test -f "$(CONTROLLER)" || { echo "Erreur : ce projet autonome ne possede pas de telecommande."; exit 1; }
	PYTHONPYCACHEPREFIX=/tmp/robotique-pycache $(PYTHON) -m py_compile "$(CONTROLLER)"

flash: check
	@test -d /Volumes/MICROBIT || { echo "Erreur : volume MICROBIT introuvable."; exit 1; }
	$(UFLASH) "$(FIRMWARE)" /Volumes/MICROBIT

install: check
	$(UFS) put "$(FIRMWARE)" main.py

run: check-controller
	$(PYTHON) "$(CONTROLLER)"

start: check-controller
	$(PYTHON) "$(CONTROLLER)" --command start

stop: check-controller
	$(PYTHON) "$(CONTROLLER)" --command stop

reset: check-controller
	$(PYTHON) "$(CONTROLLER)" --command reset

status: check-controller
	$(PYTHON) "$(CONTROLLER)" --command status

serial: check
	@test -n "$(SERIAL_PORT)" || { echo "Erreur : port serie micro:bit introuvable."; exit 1; }
	$(PYTHON) -m serial.tools.miniterm "$(SERIAL_PORT)" 115200
