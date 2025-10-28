import socket
import time
import datetime
import dns.query
import dns.message
import dns.name
import dns.rdatatype

RESOLVER_IP = '10.0.0.5'
LOG_FILE = 'resolver_log.txt'
ROOT_SERVER = '198.41.0.4' 
CACHE = {}
CACHE_TTL = 300 

def log_event(domain, mode, server_ip, step, response_type, rtt, total_time, cache_status):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    log_entry = (
        f"{timestamp}, "
        f"{domain}, "
        f"{mode}, "
        f"{server_ip}, "
        f"{step}, "
        f"{response_type}, "
        f"{rtt:.3f} ms, "
        f"{total_time:.3f} ms, "
        f"{cache_status}"
    )
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry + '\n')

def iterative_resolve(qname, qtype, start_time):
    domain = str(qname)
    qtype_str = dns.rdatatype.to_text(qtype)
    if domain in CACHE and (time.time() - CACHE[domain]['timestamp'] < CACHE_TTL):
        total_time = (time.time() - start_time) * 1000
        log_event(domain, "Iterative", RESOLVER_IP, "Cache", CACHE[domain]['rdata_type'], 0, total_time, "HIT")
        return CACHE[domain]['answer'], "HIT"
    current_server = ROOT_SERVER
    message = dns.message.make_query(qname, qtype)
    total_rtt = 0  
    for step_num in range(10):
        try:
            rtt_start = time.time()
            response = dns.query.udp(message, current_server, timeout=5.0) 
            rtt = (time.time() - rtt_start) * 1000
            total_rtt += rtt
            step_name = "Root" if current_server == ROOT_SERVER else (
                "TLD" if len(qname.labels) == 3 else "Authoritative"
            )
            if response.answer:
                answer = response.answer[0]
                answer_rdata_type = dns.rdatatype.to_text(answer.rdtype)
                CACHE[domain] = {'answer': answer, 'timestamp': time.time(), 'rdata_type': answer_rdata_type}                
                total_time = (time.time() - start_time) * 1000
                log_event(domain, "Iterative", current_server, step_name, answer_rdata_type, rtt, total_time, "MISS")                
                return response, "MISS"
            elif response.authority:
                ns_record = response.authority[0][0]
                next_server_ip = None
                for rrset in response.additional:
                    if rrset.rdtype == dns.rdatatype.A:
                        next_server_ip = str(rrset[0])
                        break                        
                if next_server_ip:
                    log_event(domain, "Iterative", current_server, step_name, f"Referral with Glue to {next_server_ip}", rtt, 0, "MISS")
                    current_server = next_server_ip
                    continue
                else:
                    ns_ip = None
                    try:
                        ns_message = dns.message.make_query(ns_record, dns.rdatatype.A)
                        ns_response = dns.query.udp(ns_message, '8.8.8.8', timeout=2.0)
                        if ns_response.answer and ns_response.answer[0].rdtype == dns.rdatatype.A:
                            ns_ip = str(ns_response.answer[0][0])
                    except Exception:
                        pass

                    if ns_ip:
                        log_event(domain, "Iterative", current_server, step_name, f"Referral (NS IP Resolved) to {ns_ip}", rtt, 0, "MISS")
                        current_server = ns_ip
                        continue
                    else:
                        log_event(domain, "Iterative", current_server, step_name, f"Failed to Resolve NS IP for {ns_record}", rtt, 0, "MISS")
                        break 
            elif response.rcode() != dns.rcode.NOERROR:
                break                
        except dns.exception.Timeout:
            log_event(domain, "Iterative", current_server, step_name if step_num > 0 else "Root", "Timeout", 5000, 0, "MISS")
            break
        except Exception:
            break  
    total_time = (time.time() - start_time) * 1000
    log_event(domain, "Iterative", current_server, "Failure", "NXDOMAIN/Timeout", total_rtt, total_time, "FAILED")
    return None, "FAILED"

def main():
    with open(LOG_FILE, 'w') as f:
        f.write("Timestamp, Domain name queried, Resolution mode, DNS server IP contacted, Step of resolution, Response or referral received, Round-trip time to that server, Total time to resolution, Cache status\n")        
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((RESOLVER_IP, 53))
    print(f"Custom DNS Resolver listening on {RESOLVER_IP}:53...")
    while True:
        try:
            data, addr = udp_socket.recvfrom(8192)
            start_time = time.time()
            request = dns.message.from_wire(data)
            qname = request.question[0].name
            qtype = request.question[0].rdtype
            response, cache_status = iterative_resolve(qname, qtype, start_time)
            if cache_status == "HIT":
                cached_answer = CACHE[str(qname)]['answer']
                reply = dns.message.make_response(request)
                reply.answer.append(cached_answer)
            elif response:
                reply = response
                reply.id = request.id 
            else:
                reply = dns.message.make_response(request)
                reply.set_rcode(dns.rcode.NXDOMAIN) 
            udp_socket.sendto(reply.to_wire(max_size=512), addr)
        except Exception as e:
            continue
        
if __name__ == '__main__':
    main()