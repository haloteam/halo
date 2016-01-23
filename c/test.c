#include <stdio.h>
#include "http-client-c.h"

int main() 
{
  printf("Testing http-post function...\n");
  struct http_response *hresp = http_post("https://a9a0t0l599.execute-api.us-east-1.amazonaws.com/prod/Halo", "", "deviceId=1");
  if(*hresp == 0) {
    printf("Post failed...\n");
  }
  else {
    printf(*hresp);
  }
  return 0;
}
