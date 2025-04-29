CFLAGS+=  -pedantic -Wall -std=c99 -O3
HW=hw04-b3b36prg
ZIP=zip
TEST_SCRIPT = test.sh

$(HW): grep.c 
	$(CC) $(CFLAGS) grep.c -o $(HW)

zip:
	$(ZIP) $(HW)-brute.zip grep.c
	
test: $(HW)
	@chmod +x $(TEST_SCRIPT)
	@./$(TEST_SCRIPT) $(HW)

clean:
	$(RM) *.o
	$(RM) $(HW)
	$(RM) $(HW)-brute.zip

.PHONY: clean zip
