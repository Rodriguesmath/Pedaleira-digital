CC ?= gcc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -Iinclude
BUILD_DIR = build

SRCS = src/inter_mcu_proto.c src/pedal_bridge.c
TEST_SRCS = tests/test_esp32_bridge.c $(SRCS)
TEST_BIN = $(BUILD_DIR)/test_esp32_bridge

.PHONY: all build test clean

all: test

build: $(TEST_BIN)

$(TEST_BIN): $(TEST_SRCS)
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ $(TEST_SRCS)

test: build
	@echo "Executing host verification suite..."
	./$(TEST_BIN)

clean:
	rm -rf $(BUILD_DIR)
