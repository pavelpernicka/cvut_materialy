#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

bool is_lowercase(char);
bool is_uppercase(char);
bool is_letter(char);
int stringlen(const char *);
char rotate(char, int);
void shift(const char *, char *, int);
int compare(const char *, const char *);
char *read_line();
char *best_shift_match(const char *, const char *, int);

int main() {
  char *encoded = read_line();         // cypher string
  char *partial_decoded = read_line(); // heard message string

  // alphabet or allocation problems
  if (!encoded || !partial_decoded) {
    fprintf(stderr, "Error: Chybny vstup!\n");
    free(encoded);
    free(partial_decoded);
    return 100;
  }

  // lengths are not equal
  int enc_len = stringlen(encoded);
  if (enc_len != stringlen(partial_decoded)) {
    fprintf(stderr, "Error: Chybna delka vstupu!\n");
    free(encoded);
    free(partial_decoded);
    return 101;
  }

  char *result = best_shift_match(encoded, partial_decoded, enc_len);

  printf("%s\n", result);

  free(encoded);
  free(partial_decoded);
  free(result);
  return 0;
}

bool is_lowercase(char c) { return c >= 'a' && c <= 'z'; }

bool is_uppercase(char c) { return c >= 'A' && c <= 'Z'; }

bool is_letter(char c) { return is_lowercase(c) || is_uppercase(c); }

int stringlen(const char *str) {
  int len = 0;
  while (*str != '\0') {
    len++;
    str++;
  }
  return len;
}

char rotate(char original, int offset) {
  /*
      Shift "original" character by "offset"
      Note: z+2 = B (not b) - alphabet is handled as whole [a-zA-Z]
  */

  int pos;

  // get relative position of shifted char
  if (is_lowercase(original)) {
    pos = (offset + (original - 'a')) % 52;
  } else if (is_uppercase(original)) {
    pos = (offset + (original - 'A') + 26) % 52;
  } else { // other char => keep
    return original;
  }

  // get char from relative position
  if (pos < 26) {
    return 'a' + pos;
  } else {
    return 'A' + (pos - 26);
  }
}

void shift(const char *src, char *dst, int offset) {
  /*
      Shift all letters in string "src" by offset, store into "dst"
  */

  int i = 0;
  while (src[i] != '\0') { // up to end of string
    dst[i] = rotate(src[i], offset);
    i++;
  }

  dst[i] = '\0'; // end new string
}

int compare(const char *str1, const char *str2) {
  /*
      Count number of letters that are same in two strings
  */
  int i = 0;
  int score = 0;

  while (str1[i] != '\0' && str2[i] != '\0') {
    if (str1[i] == str2[i]) {
      score++;
    }
    i++;
  }
  return score;
}

char *read_line() {
  /*
      Read line from stdin as string
  */

  // at begining allocate space for 15 chars
  int size = sizeof(char) * 15;
  char *new_string = malloc(size);
  if (!new_string) {
    return NULL;
  }

  int len = 0;
  int curr_char;

  // read input until it newline
  while ((curr_char = getchar()) != '\n') {
    // out of alphabet range
    if (!is_letter(curr_char)) {
      free(new_string);
      return NULL;
    }

    // reallocate double of space if last size + "\0" is used
    if (len + 1 >= size) {
      size *= 2;
      char *tmp = realloc(new_string, size);
      if (!tmp) {
        free(new_string);
        return NULL;
      }
      new_string = tmp;
    }
    new_string[len] = curr_char;
    len++;
  }

  new_string[len] = '\0';
  return new_string;
}

char *best_shift_match(const char *encoded, const char *partial, int len) {
  /*
      Find decoded message with biggest match with "partial"
  */

  char *best = malloc(len + 1);
  int best_score = -1;
  int best_shift = 0;

  // test all 2*26 shifts
  for (int i = 0; i < 52; i++) {
    shift(encoded, best, i);
    int score = compare(best, partial);
    if (score > best_score) {
      best_score = score;
      best_shift = i;
    }
  }

  // apply the best shift
  shift(encoded, best, best_shift);
  return best;
}

