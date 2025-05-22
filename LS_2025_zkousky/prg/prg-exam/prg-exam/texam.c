/*
 * File name: texam.c
 * Date:      2017/01/16 08:43
 * Author:    Jan Faigl
 */

#include <stdlib.h>

#include "exam_utils.h"

#define DEFAULT_WIDTH 640
#define DEFAULT_HEIGHT 480

int main(int argc, char *argv[]) 
{
   save_ppm_image_red(DEFAULT_WIDTH, DEFAULT_HEIGHT, "red.ppm");
   save_ppm_image_green(DEFAULT_WIDTH, DEFAULT_HEIGHT, "green.ppm");
   return EXIT_SUCCESS;
}

/* end of texam.c */
