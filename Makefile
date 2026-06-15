PROJECT ?= guidage_robot
PROJECT_DIR := $(PROJECT)
FIRMWARE := $(PROJECT_DIR)/firmware.py
CONTROLLER := $(PROJECT_DIR)/telecommande.py

PYTHON := .venv/bin/python
UFLASH := .venv/bin/uflash
UFS := .venv/bin/ufs

.PHONY: help setup check flash install run stop status serial

help:
	@echo "Projet selectionne : $(PROJECT)"
	@echo "make setup                    Cree l'environnement Python"
	@echo "make flash                    Flashe le firmware sur la micro:bit"
	@echo "make install                  Installe le firmware via le port serie"
	@echo "make run                      Lance la telecommande"
	@echo "make stop                     Arrete les moteurs"
	@echo "make status                   Affiche l'etat des moteurs"
	@echo "make serial                   Ouvre la console serie"
	@echo "make run PROJECT=autre_projet Lance un autre projet"

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install uflash microfs

check:
	@test -x "$(PYTHON)" || { echo "Erreur : lancez 'make setup'."; exit 1; }
	@test -f "$(FIRMWARE)" || { echo "Erreur : firmware introuvable : $(FIRMWARE)"; exit 1; }
	@test -f "$(CONTROLLER)" || { echo "Erreur : telecommande introuvable : $(CONTROLLER)"; exit 1; }
	PYTHONPYCACHEPREFIX=/tmp/robotique-pycache $(PYTHON) -m py_compile "$(CONTROLLER)"

flash: check
	@test -d /Volumes/MICROBIT || { echo "Erreur : volume MICROBIT introuvable."; exit 1; }
	$(UFLASH) "$(FIRMWARE)" /Volumes/MICROBIT

install: check
	$(UFS) put "$(FIRMWARE)" main.py

run: check
	$(PYTHON) "$(CONTROLLER)"

stop: check
	$(PYTHON) "$(CONTROLLER)" --command stop

status: check
	$(PYTHON) "$(CONTROLLER)" --command status

serial: check
	$(PYTHON) -m serial.tools.miniterm /dev/cu.usbmodem1302 115200
