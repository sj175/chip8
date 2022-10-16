import logging

import pygame

pygame.init()
screen = pygame.display.set_mode([640, 320])
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

op_codes = {b"00E0": "CLS", b"00EE": "RET", b"1nnn": "JP", b"2nnn": "CALL", b"3xkk": "SEVx", b"4xkk": "SNEVx"}
frame_buffer = []
registers = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0,
             11: 0, 12: 0, 13: 0, 14: 0, 15: 0}  # 8 bits each


def new_frame_buffer():
    global frame_buffer
    frame_buffer = []  # 64x32 bits each bit is a pixel
    for _ in range(32):
        frame_buffer.append([0] * 64)  # 32 rows of length 64


index_register = 0  # 16 bits
stack = []  # 64 bytes
stack_pointer = 0  # 8 bits so stack is split into 256 "slots" of 2 bytes each
delay_timer = 0  # 8 bits
sound_timer = 0  # 8 bits
program_counter = 0  # 16 bits
memory = [0] * 2048  # 4096 bytes
memory[0] = 0
memory[1] = 0


def load_file(filename):
    global program_counter
    log.debug(f"I am loading: {filename}")
    with open(filename, "rb") as file:
        file_bytes = file.read()
        for i, byte in enumerate(file_bytes):
            memory[512 + i] = byte

    # print(memory)
    program_counter = 512
    fetch_decode_execute()


def clear_screen() -> None:
    new_frame_buffer()


def set_register(register, value) -> None:
    registers[register] = value
    log.debug(f"set register: {register} to: {value}")


def add_register(register, value):
    registers[register] += value
    log.debug(f"add: {value} to register: {register}")


def get_first_nibble(byte):
    return byte >> 4


def get_second_nibble(byte):
    return ((byte >> 4) << 4) ^ byte


def set_index_register(value):
    global index_register
    index_register = value
    log.debug(f"setting index register to: {value}")


def draw(x, y, n):
    # print(f"x: {x}, y: {y}, n: {n}")
    registers[15] = 0
    start_x = registers[x] % 64
    start_y = registers[y] % 32
    for i in range(n):
        pixel_y = start_y + i
        if pixel_y > 32:
            break

        ith_byte = "{:08b}".format(memory[index_register + i])

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

    draw_frame()


def draw_frame():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

    screen.fill((255, 255, 255))
    for i, row in enumerate(frame_buffer):
        for j, bit in enumerate(frame_buffer[i]):
            if bit:
                pygame.draw.rect(screen, (0, 0, 255), pygame.Rect((i * 10, j * 10), (10, 10)), 1)

    pygame.display.flip()


def fetch_decode_execute():
    global program_counter

    while True:
        current_instruction_first_byte = memory[program_counter]
        current_instruction_second_byte = memory[program_counter + 1]
        current_instruction = (current_instruction_first_byte*256 + current_instruction_second_byte).to_bytes(2, "big")
        first_nibble = get_first_nibble(current_instruction_first_byte)
        second_nibble = get_second_nibble(current_instruction_first_byte)
        second_byte = current_instruction_second_byte
        last_three_nibbles = second_nibble * 256 + current_instruction_second_byte
        match first_nibble:
            case 0:
                match current_instruction:
                    case b"\x00\xE0":
                        clear_screen()
            case 1:
                # only support jump so far
                program_counter = last_three_nibbles
                print(f"I jumped to: {program_counter}")
                continue
            case 6:
                set_register(second_nibble, second_byte)
            case 7:
                add_register(second_nibble, second_byte)
            case 10:
                set_index_register(last_three_nibbles)
            case 13:
                draw(second_nibble, get_first_nibble(current_instruction[1]), get_second_nibble(current_instruction[1]))
            case _:
                print(f"FATAL ERROR: {current_instruction} is not a recognised opcode")

        program_counter += 2

        # print(program_counter)
        # draw_frame()
        # break


if __name__ == '__main__':
    # fetch_decode_execute()
    load_file("ibm-logo.ch8")
