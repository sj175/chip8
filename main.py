import logging

import pygame

pygame.init()
screen = pygame.display.set_mode([640, 320])
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

op_codes = {b"00E0": "CLS", b"00EE": "RET", b"1nnn": "JP", b"2nnn": "CALL", b"3xkk": "SEVx", b"4xkk": "SNEVx"}

registers = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0,
             11: 0, 12: 0, 13: 0, 14: 0, 15: 0}  # 8 bits each

index_register = 0  # 16 bits
stack = []  # 64 bytes
stack_pointer = 0  # 8 bits so stack is split into 256 "slots" of 2 bytes each
delay_timer = 0  # 8 bits
sound_timer = 0  # 8 bits
frame_buffer = []  # 64x32 bits each bit is a pixel
program_counter = 0  # 16 bits
memory = [b"\xda\xbf"] * 4096  # 4096 bytes


def load_file(filename):
    global program_counter
    print(f"I would be loading: {filename}")
    with open(filename, "rb") as file:
        print(file.read())
    program_counter = 512
    # fetch_decode_execute()


def clear_screen():
    print("clear screen!")


def set_register(register, value):
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
    pixel_x = registers[x] % 64
    pixel_y = registers[y] % 32
    registers[15] = 0
    for i in range(n):
        ith_byte = memory[index_register]
        #do some shit


def draw_frame():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

    screen.fill((255, 255, 255))
    pygame.draw.rect(screen, (0, 0, 255), pygame.Rect((0, 0), (30, 30)), 75)
    pygame.display.flip()


def fetch_decode_execute():
    global program_counter

    while True:
        current_instruction = memory[program_counter]
        first_nibble = get_first_nibble(current_instruction[0])
        second_nibble = get_second_nibble(current_instruction[0])
        second_byte = current_instruction[1]
        last_three_nibbles = second_nibble * 256 + current_instruction[1]
        match first_nibble:
            case 0:
                match current_instruction:
                    case b"\x00\xE0":
                        clear_screen()
            case 1:
                # only support jump so far
                program_counter = current_instruction
                print(f"I jumped to: {program_counter}")
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

        # print(program_counter)
        draw_frame()


if __name__ == '__main__':
    fetch_decode_execute()
    # load_file("ibm-logo.ch8")
