/*
 * File name: xwin_sdl.h
 * Date:      2015/06/18 14:37
 * Author:    Jan Faigl
 */

#ifndef __XWIN_SDL_H__
#define __XWIN_SDL_H__

/* 
 * Initialize window  w x h
 */
int xwin_init(int w, int h);

/*
 * close the window and release memory
 */ 
void xwin_close(void);

/*
 * draw image as a sequence of RGB values to the window
 * xwin_init must be called first
 */ 
void xwin_redraw(int w, int h, unsigned char *img);

void delay(int ms);

/*
 * poll all events eventually pushed into the sdl event queue
 */
void xwin_poll_events(void);

/*
 * load image using sdl_image
 */
unsigned char *xwin_load_image(const char *filename, int *width, int *height);

// return pointer to the image data or NULL on error that can be
// - file has not been loaded or does not contain image with 32-bits per pixel.
// - memory allocation fail
// An error message is reported on the stderr 
// New memory is allocated and should be release out of the function.
unsigned char *xwin_load_image_rgba(const char *filename, size_t *size);

#endif

/* end of xwin_sdl.h */
