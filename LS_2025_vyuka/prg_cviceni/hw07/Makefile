CFLAGS+= -Wall -Werror -std=c99 -g
TEST_SCRIPT = test.sh
HW=hw07

BINARIES=hw07-test hw07-testopt-int hw07-testopt-str hw07-testopt-stc
all: $(BINARIES)

hw07-man: hw07-test

hw07-opt: hw07-testopt-int hw07-testopt-str hw07-testopt-stc

hw07-test: hw07-test.c linked_list.o
	$(CC) $(CFLAGS) hw07-test.c linked_list.o -o $@

hw07-testopt-int: hw07-testopt-int.c queue.o
	$(CC) $(CFLAGS) hw07-testopt-int.c queue.o -o $@

hw07-testopt-str: hw07-testopt-str.c queue.o
	$(CC) $(CFLAGS) hw07-testopt-str.c queue.o -o $@

hw07-testopt-stc: hw07-testopt-stc.c queue.o
	$(CC) $(CFLAGS) hw07-testopt-stc.c queue.o -o $@

linked_list.o: linked_list.c 
	$(CC) -c $(CFLAGS) $< -o $@

queue.o: queue.c 
	$(CC) -c $(CFLAGS) $< -o $@
	
zip:
	zip $(HW)-brute.zip linked_list.c queue.c
	
testman:
	@chmod +x $(TEST_SCRIPT)
	@./$(TEST_SCRIPT) hw07-test man
	
testopt:
	@chmod +x $(TEST_SCRIPT)
	@echo "Running tests for int:"
	@./$(TEST_SCRIPT) hw07-testopt-int opt.int
	@echo "Running tests for stc:"
	@./$(TEST_SCRIPT) hw07-testopt-stc opt.stc
	@echo "Running tests for str:"
	@./$(TEST_SCRIPT) hw07-testopt-str opt.str
	
test: testman testopt

clean:
	rm -f *.o $(BINARIES)
	rm -f $(HW)-brute.zip
