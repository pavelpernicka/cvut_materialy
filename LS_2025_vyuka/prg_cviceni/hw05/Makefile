CFLAGS+=  -pedantic -Wall -std=c99 -O3
HW=hw05-b3b36prg
ZIP=zip
TEST_SCRIPT = test.sh

$(HW): main.c 
	$(CC) $(CFLAGS) main.c -o $(HW)

zip:
	$(ZIP) $(HW)-brute.zip main.c

test: $(HW)
	@chmod +x $(TEST_SCRIPT)
	@./$(TEST_SCRIPT) $(HW)
	
clean:
	$(RM) *.o
	$(RM) $(HW)
	$(RM) $(HW)-brute.zip

.PHONY: clean zip
