#include <cstdio>
#include <cstdlib>
#include <unistd.h>
#include <bmpd/switch/pd/pd.h>
#include <bm/pdfixed/pd_static.h>
#include <switchapi/switch_base_types.h>

extern "C" {
    extern int start_switch_api_rpc_server(void);
    extern int api_rpc_port;
}

using namespace std;

int main(int argc, char **argv) {
    if (argc != 4) {
        printf("Expected arguments: <switchapi-rpc-port> <bmv2-thrift-port> <bmv2-ipc-address>\n");
        return 1;
    }

    api_rpc_port = atoi(argv[1]);
    if (api_rpc_port <= 0) {
        printf("Invalid <switchapi-rpc-port> argument.\n");
        return 1;
    }

    int bmv2_thrift_port = atoi(argv[2]);
    if (bmv2_thrift_port <= 0) {
        printf("Invalid <bmv2-thrift-port> argument.\n");
        return 1;
    };

    char *bmv2_ipc_address = argv[3];

    p4_pd_init();
    p4_pd_dc_init();
    p4_pd_dc_assign_device(0, bmv2_ipc_address, bmv2_thrift_port);

    if (switch_api_init(0, 256) < 0) {
        printf("Failed to initialize SwitchAPI.\n");
        return 1;
    }

    if (start_switch_api_rpc_server() < 0) {
        printf("Failed to start SwitchAPI RPC server.\n");
        return 1;
    }

    pause();

    return 0;
}