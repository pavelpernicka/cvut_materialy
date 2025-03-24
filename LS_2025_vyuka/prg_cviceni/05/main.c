#include <stdio.h>

int main(int argc, char const *argv[]){
    /*
    int delka = 0;
    scanf("%d", &delka);
    int pole[delka];
    for(int = 0, i < delka, i++){
      scanf("%d", &pole[i];
    }
    
    for(int i=0; i < delka; i++){
      printf("%d", pole[i]);
    }
    */

    int delka = sizeof(argv)/sizeof(argv[1]);
    for(int i = 1; i < delka; i++){
        printf(argv[i]);
    }

    return 0;
}
