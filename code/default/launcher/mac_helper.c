#include <stdio.h>
#include <string.h>
#include <unistd.h>

// Don't pass the caller's environment (e.g. DYLD_*) to a root process.
static char *const clean_env[] = {"PATH=/usr/bin:/bin:/usr/sbin:/sbin", NULL};

int main(int argc, const char * argv[]) {
    if (geteuid() != 0) {
        fprintf(stderr, "Must be run as root!\n");
        return 1;
    }
    // Setuid only gives us the effective uid; networksetup spawns cp to back up
    // preferences.plist, which then runs as the real (normal) user and fails.
    if (setgid(0) != 0 || setuid(0) != 0) {
        perror("setuid");
        return 1;
    }
    if (argc == 4 && strcmp(argv[1], "enableauto") == 0) {
        execle("/usr/sbin/networksetup", "networksetup", "-setautoproxyurl", argv[2], argv[3], NULL, clean_env);
    } else if (argc == 5 && strcmp(argv[1], "enablehttp") == 0) {
        execle("/usr/sbin/networksetup", "networksetup", "-setwebproxy", argv[2], argv[3], argv[4], NULL, clean_env);
    } else if (argc == 5 && strcmp(argv[1], "enablehttps") == 0) {
        execle("/usr/sbin/networksetup", "networksetup", "-setsecurewebproxy", argv[2], argv[3], argv[4], NULL, clean_env);
    } else if (argc == 3 && strcmp(argv[1], "disableauto") == 0) {
        execle("/usr/sbin/networksetup", "networksetup", "-setautoproxystate", argv[2], "off", NULL, clean_env);
    } else if (argc == 3 && strcmp(argv[1], "disablehttp") == 0) {
        execle("/usr/sbin/networksetup", "networksetup", "-setwebproxystate", argv[2], "off", NULL, clean_env);
    } else if (argc == 3 && strcmp(argv[1], "disablehttps") == 0) {
        execle("/usr/sbin/networksetup", "networksetup", "-setsecurewebproxystate", argv[2], "off", NULL, clean_env);
    } else {
        fprintf(stderr, "Usage:\n");
        fprintf(stderr, "%s enableauto <networkservice> <url>\n", argv[0]);
        fprintf(stderr, "%s enablehttp <networkservice> <domain> <port number>\n", argv[0]);
        fprintf(stderr, "%s enablehttps <networkservice> <domain> <port number>\n", argv[0]);
        fprintf(stderr, "%s disableauto <networkservice>\n", argv[0]);
        fprintf(stderr, "%s disablehttp <networkservice>\n", argv[0]);
        fprintf(stderr, "%s disablehttps <networkservice>\n", argv[0]);
    }
    return 0;
}
