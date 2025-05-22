#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#define MAX 1000000      // 10^6
#define NUM_PRIMES 79000 // expected number of primes < MAX

int primes[NUM_PRIMES];
int prime_count = 0;

void prepare_primes();
void decompose_number();

int main(void) {
  /*
    Loads numbers from stdin and decomposes them if they are valid.
    Eratosthenes sieve is used to prepare array of primes for faster decomposition.
  */

  prepare_primes();
  long long n; // >= 64-bit signed number

  while (1) {
    int result = scanf("%lld", &n);

    if (result != 1 || n < 0) {
      fprintf(stderr, "Error: Chybny vstup!\n");
      return 100;
    }

    if (n == 0) { // end number loading loop if zero occurs
      break;
    }

    decompose_number(n);
  }

  return 0;
}

void prepare_primes() {
  /*
    Prepares array of prime numbers up to MAX using Eratosthenes sieve method
  */
  bool excluded_from_prime[MAX] = {false};

  // check all numbers up to MAX
  for (int i = 2; i < MAX; i++) {
    if (!excluded_from_prime[i]) { // if not excluded, assume it is prime
      primes[prime_count++] = i;

      // exclude all multiples of discovered prime
      for (int mul = i + i; mul < MAX; mul += i) {
        excluded_from_prime[mul] = true;
      }
    }
  }
}

void decompose_number(long long n) {

  if (n == 1) {
    printf("Prvociselny rozklad cisla 1 je:\n1\n");
    return;
  }

  printf("Prvociselny rozklad cisla %lld je:\n", n);
  int first_mul = 1;

  // go through precalculated primes
  for (int i = 0; i < prime_count && (long long)primes[i] * primes[i] <= n; ++i) {
    int factor = 0;

    // count factor of currently processed prime
    while (n % primes[i] == 0) {
      n /= primes[i];
      factor++;
    }

    // print prime and factor in correct form
    if (factor > 0) {
      if (!first_mul) {
        printf(" x ");
      }
      first_mul = 0;
      if (factor == 1) {
        printf("%d", primes[i]);
      } else {
        printf("%d^%d", primes[i], factor);
      }
    }
  }

  // add remainder to decomposition chain
  if (n > 1) {
    if (!first_mul) {
      printf(" x ");
    }
    printf("%lld", n);
  }

  printf("\n");
}

