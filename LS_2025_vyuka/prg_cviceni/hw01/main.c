#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#define MIN_SIZE 3
#define MAX_SIZE 69

void print_repeat(char what, int times) {
/*
  Repeats char x times
  - what: charto repeat
  - times: number of repeats
*/
	for (int i = 0; i < times; i++) putchar(what);
}

void draw_fence_row(int fence_size, bool is_base) {
/*
  Draws one line of fence according to its type
  - fence_size: num of fence characters
  - is_base: true => filled fence, otherwise normal fence
*/
    char fill = ' ';
    if(is_base) {
       	fill = '-';
    }
    for (int j = 0; j < fence_size; j++) {
        // toggle fencing style at odd/even iterator; odd fence_size => inverze style, '|' must be at the end
        putchar((j % 2 == fence_size % 2) ? fill : '|');
    }
    printf("\n");
}

void draw_roof_row(int trailing_spaces, int width) {
/*
  Draws one line of roof
  - trailing_spaces: num of spaces before roof block
  - width: size of roof block
*/
    print_repeat(' ', trailing_spaces);
    printf("X");
    if (width > 1) {
        print_repeat(' ', width - 2);
        printf("X");
    }
    printf("\n");
}

void draw_roof(int width) {
/*
  Draws triangle of roof (without top base)
*/
    int trailing_spaces = width / 2;
    for (int i = 0; i < width / 2; i++) {
        draw_roof_row(trailing_spaces, 2 * i + 1); 
        trailing_spaces--;
    }
}

void draw_full_base(int width) {
/*
  Draws top/bottom base of the house
*/
    print_repeat('X', width);
}

void draw_body(int width, int height, int fence_size) {
/*
  Draws internal blocks of house
  - width: house width
  - height: house height
  - fence_size: set both x and y sizes of fence
*/
    bool first_fence_row = true;
    for (int i = 0; i < height; i++) {
        printf("X");
        for (int j = 1; j < width - 1; j++) {
        	if(fence_size == 0){ // when no fence, house is not filled
        		printf(" ");
        	}else if((i + j) % 2 == 0){ // when there isfence, repeat o*o pattern (each line has offset)
            	printf("*");
            }else{
                printf("o");
            }
        }
        printf("X");
        
        // decide to draw a fence or end house boundary
        if(fence_size != 0 && i > height-fence_size){ // start drawing fence from this line
        	draw_fence_row(fence_size, first_fence_row);
        	first_fence_row = false;
        }else{
        	printf("\n");
        }
    }
}

int main() {
/*
  Entry function 
*/
    int width, height, fence_size = 0;
    
    if (scanf("%d %d", &width, &height) != 2) { // expecting 2 fields to be processed
        fprintf(stderr, "Error: Chybny vstup!\n");
        return 100;
    }
    if (width < MIN_SIZE || width > MAX_SIZE || height < MIN_SIZE || height > MAX_SIZE) {
        fprintf(stderr, "Error: Vstup mimo interval!\n");
        return 101;
    }
    if (width % 2 == 0) {
        fprintf(stderr, "Error: Sirka neni liche cislo!\n");
        return 102;
    }
    if (width == height) { // when 1:1 ratio, try to load third value
        if (scanf("%d", &fence_size) != 1) {
            fprintf(stderr, "Error: Chybny vstup!\n");
            return 100;
        }
        if (fence_size <= 0 || fence_size >= height) {
            fprintf(stderr, "Error: Neplatna velikost plotu!\n");
            return 103;
        }
    }
    
    draw_roof(width); // roof triangle
    draw_full_base(width); printf("\n"); // XXXXX-like base with newline
    draw_body(width, height - 2, fence_size); // body of size without 2 externaly added bases
    draw_full_base(width); // XXXXX-like line
    draw_fence_row(fence_size, true); // fence for the last row
    
    return 0;
}
