.PHONY: all flash reset term

PIDFILE ?= /tmp/riotctrl_test_pid
CTRLPID = $(shell cat $(firstword $(wildcard $(PIDFILE)) /dev/null))

CTRL_WRAPPER ?= ./ctrl.py
APPLICATION ?= ./echo.py

ifeq (1,$(QUIET))
  Q=@
else
  Q=
endif

all:
flash:

reset:
	kill -USR1 $(CTRLPID) 2>/dev/null || true

term:
	$(Q)sh -c 'echo $$$$ > $(PIDFILE); exec $(CTRL_WRAPPER) $(APPLICATION)'
