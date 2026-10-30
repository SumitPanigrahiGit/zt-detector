// attack.c - harmless simulation of the syscalls used in process injection.
// Runs no payload: it only makes the calls so the tracer can see them.
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ptrace.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

int main(int argc, char **argv)
{
    int target = argc > 1 ? atoi(argv[1]) : 1;

    // 1) ptrace: attach to the target and detach again
    ptrace(PTRACE_SEIZE, target, 0, 0);
    ptrace(PTRACE_DETACH, target, 0, 0);
    puts("step 1: ptrace seize/detach");

    // 2) writable memory made executable
    void *p = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    mprotect(p, 4096, PROT_READ | PROT_WRITE | PROT_EXEC);
    puts("step 2: mmap RW -> mprotect RWX");

    // 3) connect to an unusual destination (non-blocking: returns at once)
    int s = socket(AF_INET, SOCK_STREAM, 0);
    fcntl(s, F_SETFL, O_NONBLOCK);
    struct sockaddr_in a = { .sin_family = AF_INET, .sin_port = htons(4444) };
    inet_pton(AF_INET, "1.1.1.1", &a.sin_addr);
    connect(s, (struct sockaddr *)&a, sizeof(a));
    close(s);
    puts("step 3: connect 1.1.1.1:4444");

    // 4) spawn a shell
    puts("step 4: spawn /bin/sh");
    fflush(stdout);
    execl("/bin/sh", "sh", "-c", "id", (char *)NULL);
    return 0;
}

