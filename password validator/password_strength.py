import pygame

# initialize pygame
pygame.init()
screen = pygame.display.set_mode((1000, 200))
pygame.display.set_caption("Press to start...")
CLOCK = pygame.time.Clock()

# text widget
text = "write here..."
text_font = pygame.font.Font('freesansbold.ttf', 100)
text_font_mid = text_font.render(text, True, (0, 0, 0))
text_rect = text_font_mid.get_rect().center = (50, 50)
enter = 0


# password strength
def pass_strength(password):
    capitalize = False
    no_repeat = True
    number = False
    special_character = False
    for i, counter in zip(password, range(len(password))):
        if i.upper() == i:
            capitalize = True
        if len(password) > 2:
            if i == password[counter-1]:
                no_repeat = False
        try:
            int(i)
            number = True
        except:
            # not a number
            pass
        if i in '''!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~''':
            special_character = True
    if capitalize and no_repeat and number and special_character and 7 < len(text) < 14:
        return 0
    elif not no_repeat:
        return 3
    elif not capitalize:
        return 4
    elif not number:
        return 2
    elif not special_character:
        return 1
    elif len(text) > 13:
        return 5
    elif len(text) < 8:
        return 6


strength_font = pygame.font.Font('freesansbold.ttf', 12)
strength_text = strength_font.render("", True, (255, 0, 0))
strength_rect = strength_text.get_rect().center = (50, 150)

# run loop
run = True
text_input = True
while run:
    screen.fill((255, 255, 255))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            text_input = True
            print("mouse down")
            if enter == 0:
                text = ""
            enter += 1
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                text_input = False
        if event.type == pygame.KEYDOWN and text_input:
            if event.key == pygame.K_BACKSPACE:
                text = text[:-1]
                text_font_mid = text_font.render(text, True, (0, 0, 0))
                if enter != 0:
                    strength_text = strength_font.render("", True, (59, 176, 66))
                    match pass_strength(text):
                        case 0:
                            strength_text = strength_font.render("password is strong!", True, (59, 176, 66))
                            break
                        case 1:
                            strength_text = strength_font.render("special letter missing", True, (255, 0, 0))
                            break
                        case 2:
                            strength_text = strength_font.render("number missing", True, (255, 0, 0))
                            break
                        case 3:
                            strength_text = strength_font.render("there are two identical letters", True, (255, 0, 0))
                            break
                        case 4:
                            strength_text = strength_font.render("capital letter missing", True, (255, 0, 0))
                            break
                        case 5:
                            strength_text = strength_font.render("password too long", True, (255, 0, 0))
                            break
                        case 6:
                            strength_text = strength_font.render("password too short", True, (255, 0, 0))
                            break
                else:
                    pass
            else:
                text += event.unicode
                text_font_mid = text_font.render(text, True, (0, 0, 0))
                if enter != 0:
                    strength_text = strength_font.render("", True, (59, 176, 66))
                    screen.blit(strength_text, strength_rect)
                    match pass_strength(text):
                        case 0:
                            strength_text = strength_font.render("password is strong!", True, (59, 176, 66))
                            break
                        case 1:
                            strength_text = strength_font.render("special letter missing", True, (255, 0, 0))
                            break
                        case 2:
                            strength_text = strength_font.render("number missing", True, (255, 0, 0))
                            break
                        case 3:
                            strength_text = strength_font.render("there are two identical letters", True, (255, 0, 0))
                            break
                        case 4:
                            strength_text = strength_font.render("capital letter missing", True, (255, 0, 0))
                            break
                        case 5:
                            strength_text = strength_font.render("password too long", True, (255, 0, 0))
                            break
                        case 6:
                            strength_text = strength_font.render("password too short", True, (255, 0, 0))
                            break
                else:
                    pass
    screen.blit(text_font_mid, text_rect)
    screen.blit(strength_text, strength_rect)
    CLOCK.tick(20)
    pygame.display.flip()
pygame.quit()
exit()
