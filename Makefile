.PHONY: flash serial remote remote-stop remote-status

FLASH_FILE := $(or $(firstword $(filter %.py,$(MAKECMDGOALS))),microbit_test.py)

flash:
	@test -f "$(FLASH_FILE)" || { echo "Erreur : fichier introuvable : $(FLASH_FILE)"; exit 1; }
	.venv/bin/uflash "$(FLASH_FILE)" /Volumes/MICROBIT

serial:
	.venv/bin/python -m serial.tools.miniterm /dev/cu.usbmodem1302 115200

remote:
	.venv/bin/python remote_control.py

remote-stop:
	.venv/bin/python remote_control.py --command stop

remote-status:
	.venv/bin/python remote_control.py --command status

# Permet d'utiliser un fichier Python comme argument : make flash programme.py
%.py:
	@:
