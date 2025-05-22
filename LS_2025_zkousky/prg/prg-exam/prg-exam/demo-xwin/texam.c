/*
 * File name: texam.c
 * Date:      2017/01/16 17:00
 * Author:    Jan Faigl
 */

#include <stdio.h>
#include <stdlib.h>

#include "exam_utils.h"
#include "save_jpeg.h"
#include "xwin_sdl.h"

#define WIDTH 640
#define HEIGHT 480

static int anim = 200;

int main(int argc, char *argv[])
{
   save_ppm_image_red(WIDTH, HEIGHT, "red.ppm");
   save_ppm_image_green(WIDTH, HEIGHT, "green.ppm");

   unsigned char *img = (unsigned char*)malloc(sizeof(unsigned char)* 3 * WIDTH * HEIGHT);
   my_assert(img != NULL, __func__, __LINE__, __FILE__);

   // create red image
   unsigned char *cur = img;
   for (int y = 0; y < HEIGHT; ++y) {
      for (int x = 0; x < WIDTH; ++x) {
	 *(cur++) = 255; // R
	 *(cur++) = 0; // G
	 *(cur++) = 0; // B
      }
   }

   // save image as jpeg
   save_image_jpeg(WIDTH, HEIGHT, img,  "red.jpg");

   // create animation 
   xwin_init(WIDTH, HEIGHT); // initialize x-window
   for (int i = 0; i < anim; ++i) {

      // create an image
      for (int y = 0; y < HEIGHT; ++y) {
	 for (int x = 0; x < WIDTH; ++x) {
	    const int idx = y * WIDTH * 3 + x * 3; // compute the pixel position
	    *(img + idx + 0) = (y + i)% 255; // R
	    *(img + idx + 1) = 0; // G
	    *(img + idx + 2) = 0; // B
	 }
      }

      xwin_redraw(WIDTH, HEIGHT, img); // draw the image to the window
      delay(10); // wait for 10 ms. It is not necessary for visualization of the Julia set, which is computationally demanding
   }
   xwin_close();
   free(img);
   return EXIT_SUCCESS;
}

/* end of texam.c */
