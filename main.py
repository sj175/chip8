import logging
import sys
import time

import pygame

BILLION = 1000000000
COSMIC = "COSMAC_VIP"
TYPE = "SUPER_CHIP"
INDEX_REGISTER = "index"

pygame.init()
screen = pygame.display.set_mode([640, 320])
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

op_codes = {b"00E0": "CLS", b"00EE": "RET", b"1nnn": "JP", b"2nnn": "CALL", b"3xkk": "SEVx", b"4xkk": "SNEVx"}
frame_buffer = []
registers = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0,
             11: 0, 12: 0, 13: 0, 14: 0, 15: 0, INDEX_REGISTER: 0}  # 8 bits each


def new_frame_buffer():
    global frame_buffer
    frame_buffer = []  # 64x32 bits each bit is a pixel
    for _ in range(32):
        frame_buffer.append([0] * 64)  # 32 rows of length 64


stack = []  # 64 bytes
stack_pointer = 0  # 8 bits so stack is split into 256 "slots" of 2 bytes each
delay_timer = 0  # 8 bits
sound_timer = 0  # 8 bits
program_counter = 0  # 16 bits
memory = [0] * 4096  # 4096 bytes
memory[0] = 0
memory[1] = 0
memory[511] = 0  # ***** THIS IS A TEST REMEMBER TO REMOVE ME ****
new_frame_buffer()

timer = time.perf_counter_ns()


def load_file(filename) -> None:
    global program_counter
    log.debug(f"I am loading: {filename}")
    with open(filename, "rb") as file:
        file_bytes = file.read()
        for i, byte in enumerate(file_bytes):
            memory[512 + i] = byte

    program_counter = 512
    fetch_decode_execute()


def clear_screen() -> None:
    new_frame_buffer()


def set_register(register, value) -> None:
    registers[register] = value
    log.debug(f"set register: {register} to: {value}")


def add_register(register, value) -> None:
    registers[register] += value
    registers[register] %= 256
    log.debug(f"add: {value} to register: {register}")


def get_first_nibble(byte) -> int:
    return byte >> 4


def get_second_nibble(byte) -> int:
    return ((byte >> 4) << 4) ^ byte


def set_index_register(value) -> None:
    registers[INDEX_REGISTER] = value
    log.debug(f"setting index register to: {value}")


def draw(x, y, n) -> None:
    registers[15] = 0
    start_x = registers[x] % 64
    start_y = registers[y] % 32
    for i in range(n):
        pixel_y = start_y + i
        if pixel_y > 32:
            break

        ith_byte = "{:08b}".format(memory[registers[INDEX_REGISTER] + i])

        for j in range(8):
            pixel_x = start_x + j
            if pixel_x > 64:
                break

            sprite_bit = int(ith_byte[j])
            screen_bit = int("{:08b}".format(frame_buffer[pixel_y][pixel_x])[j])
            if sprite_bit ^ screen_bit:
                if sprite_bit and screen_bit:
                    registers[15] = 1
                frame_buffer[pixel_y][pixel_x] = 1


def draw_frame() -> None:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

    screen.fill((255, 255, 255))
    for i, row in enumerate(frame_buffer):
        for j, bit in enumerate(frame_buffer[i]):
            if bit:
                pygame.draw.rect(screen, (0, 0, 255), pygame.Rect((j * 10, i * 10), (10, 10)), 0)

    pygame.display.flip()


def unknown_instruction(current_instruction) -> None:
    quit(f"FATAL ERROR: {current_instruction} is not a recognised opcode")


def quit(message: str) -> None:
    log.error(message)
    pygame.quit()
    sys.exit(1)


def fetch_decode_execute() -> None:
    global program_counter, timer, delay_timer, sound_timer, memory
    cpu_cycles = 0

    while True:
        # ####### this block is for going slow
        # current_time = time.perf_counter_ns()
        # if current_time - timer < BILLION:
        #     time.sleep((BILLION - (current_time - timer)) / BILLION)
        #     timer = time.perf_counter_ns()
        # #######

        if cpu_cycles % 1000 == 0:
            draw_frame()
        current_instruction_first_byte = memory[program_counter]
        current_instruction_second_byte = memory[program_counter + 1]
        current_instruction = (current_instruction_first_byte * 256 + current_instruction_second_byte).to_bytes(2,
                                                                                                                "big")
        first_nibble = get_first_nibble(current_instruction_first_byte)
        second_nibble = get_second_nibble(current_instruction_first_byte)
        second_byte = current_instruction_second_byte
        third_nibble = get_first_nibble(current_instruction_second_byte)
        fourth_nibble = get_second_nibble(current_instruction_second_byte)
        last_three_nibbles = second_nibble * 256 + current_instruction_second_byte
        match first_nibble:
            case 0:
                match current_instruction:
                    case b"\x00\xE0":
                        clear_screen()
                    case b"\x00\xEE":
                        program_counter = stack.pop()
            case 1:
                program_counter = last_three_nibbles
                log.debug(f"I jumped to: {program_counter}")
                cpu_cycles += 1
                continue
            case 2:
                stack.append(program_counter)
                program_counter = last_three_nibbles
                log.debug(f"I jumped to: {program_counter} and pushed {stack[-1]} to the stack")
            case 3:
                if registers[second_nibble] == second_byte:
                    program_counter += 2
            case 4:
                # She jumped like JNE up onto my erection I picked up that ho like straight garbage collection
                if registers[second_nibble] != second_byte:
                    program_counter += 2
            case 5:
                if fourth_nibble != 0:
                    unknown_instruction(current_instruction)
                if registers[second_nibble] == registers[third_nibble]:
                    program_counter += 2
            case 6:
                set_register(second_nibble, second_byte)
            case 7:
                add_register(second_nibble, second_byte)
            case 8:
                match fourth_nibble:
                    case 0:
                        registers[second_nibble] = registers[third_nibble]
                    case 1:
                        registers[second_nibble] = registers[second_nibble] | registers[third_nibble]
                    case 2:
                        registers[second_nibble] = registers[second_nibble] & registers[third_nibble]
                    case 3:
                        registers[second_nibble] = registers[second_nibble] ^ registers[third_nibble]
                    case 4:
                        if registers[second_nibble] + registers[third_nibble] > 255:
                            carry_bit = 1
                        else:
                            carry_bit = 0
                        registers[second_nibble] = (registers[second_nibble] + registers[third_nibble]) % 256
                        registers[15] = carry_bit
                    case 5:
                        if registers[second_nibble] > registers[third_nibble]:
                            carry_bit = 1
                        else:
                            carry_bit = 0
                        registers[second_nibble] = (registers[second_nibble] - registers[third_nibble]) % 256
                        registers[15] = carry_bit
                    case 6:
                        if TYPE == COSMIC:
                            registers[second_nibble] = registers[third_nibble]
                        carry_bit = registers[second_nibble] & 1  # select LSB
                        registers[second_nibble] >>= 1
                        registers[15] = carry_bit
                    case 7:
                        if registers[third_nibble] > registers[second_nibble]:
                            carry_bit = 1
                        else:
                            carry_bit = 0
                        registers[second_nibble] = (registers[third_nibble] - registers[second_nibble]) % 256
                        registers[15] = carry_bit
                    case 14:
                        if TYPE == COSMIC:
                            registers[second_nibble] = registers[third_nibble]
                        carry_bit = (registers[second_nibble] & 128) >> 7  # select 8-bit MSB
                        registers[second_nibble] <<= 1
                        registers[15] = carry_bit
            case 9:
                if fourth_nibble != 0:
                    unknown_instruction(current_instruction)
                if registers[second_nibble] != registers[third_nibble]:
                    program_counter += 2
            case 10:
                set_index_register(last_three_nibbles)
            case 13:
                draw(second_nibble, get_first_nibble(current_instruction[1]), get_second_nibble(current_instruction[1]))
            case 15:
                match second_byte:
                    case 7:
                        registers[second_nibble] = delay_timer
                    case 10:
                        pass  # wait for key input
                    case 15:
                        delay_timer = registers[second_nibble]
                    case 18:
                        sound_timer = registers[second_nibble]
                    case 30:
                        add_register(INDEX_REGISTER, registers[second_nibble])  # need to implement overflow
                    case 51:
                        num = registers[second_nibble]
                        addr = registers[INDEX_REGISTER]
                        memory[addr] = num % 10
                        memory[addr + 1] = num // 10 % 10
                        memory[addr + 2] = num // 100 % 10
                    case 85:
                        # implement ambiguity switch
                        for i in range(second_nibble):
                            memory[registers[INDEX_REGISTER] + i] = registers[i]
                    case 101:
                        # implement ambiguity switch
                        for i in range(second_nibble):
                            registers[i] = memory[registers[INDEX_REGISTER] + i]
            case _:
                log.error(f"FATAL ERROR: {current_instruction} is not a recognised opcode")
                quit(f"FATAL ERROR: {current_instruction} is not a recognised opcode")

        cpu_cycles += 1
        program_counter += 2

    log.error("unhandled error, mainloop interrupted")


if __name__ == '__main__':
    # load_file("ibm-logo.ch8")
    # load_file("test_opcode.ch8")
    load_file("chip8-test-suite.ch8")
