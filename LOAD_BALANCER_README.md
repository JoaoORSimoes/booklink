# BookLink Load Balancer Implementation

## Visão Geral

Este projeto implementa um load balancer NGINX para o sistema BookLink, uma arquitetura de microserviços que inclui serviços de usuários, catálogo, reservas e pagamentos. O load balancer distribui as requisições de forma equilibrada entre os serviços e fornece monitoramento em tempo real.

## Arquitetura do Load Balancer

### Componentes Principais

1. **NGINX Load Balancer**
   - Distribui requisições entre os microserviços
   - Configurado com algoritmo round-robin
   - Exposição em duas portas: 80 (aplicação) e 8080 (monitoramento)

2. **Sistema de Monitoramento**
   - Health checks automáticos
   - Estatísticas em tempo real
   - Dashboard de monitoramento

3. **Microserviços Backend**
   - User Service (porta 5001)
   - Catalog Service (porta 5002)
   - Reservation Service (porta 5003)
   - Payment Service (porta 5004)

## Configuração do NGINX

### Estrutura de Arquivos

```
nginx/
├── nginx.conf                 # Configuração principal
└── conf.d/
    └── basic_lb.conf         # Configuração do load balancer
```

### Configuração Principal (`nginx/nginx.conf`)

```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                   '$status $body_bytes_sent "$http_referer" '
                   '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;
    
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    include /etc/nginx/conf.d/*.conf;
}
```

### Configuração do Load Balancer (`nginx/conf.d/basic_lb.conf`)

```nginx
# Upstream definitions for each microservice
upstream user_service {
    server user_service:5001;
}

upstream catalog_service {
    server catalog_service:5002;
}

upstream reservation_service {
    server reservation_service:5003;
}

upstream payment_service {
    server payment_service:5004;
}

# Main server block for application traffic (port 80)
server {
    listen 80;
    server_name localhost;
    
    # User service routes
    location /users {
        proxy_pass http://user_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Catalog service routes
    location /books {
        proxy_pass http://catalog_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Reservation service routes
    location /reservations {
        proxy_pass http://reservation_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Payment service routes
    location /payments {
        proxy_pass http://payment_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check endpoint
    location /health {
        return 200 "Load Balancer OK\n";
        add_header Content-Type text/plain;
    }
}

# Monitoring server block (port 8080)
server {
    listen 8080;
    server_name localhost;
    
    # NGINX status page
    location /nginx_status {
        stub_status on;
        access_log off;
        allow all;
    }
    
    # Monitoring dashboard
    location /monitor {
        return 200 "NGINX Load Balancer Monitoring\nAccess /nginx_status for detailed stats\n";
        add_header Content-Type text/plain;
    }
}
```

## Docker Compose Configuration

### Arquivo `docker-compose.step1.yml`

```yaml
version: '3.8'

services:
  # NGINX Load Balancer
  nginx:
    image: nginx:alpine
    container_name: booklink_nginx_lb
    ports:
      - "80:80"      # Application traffic
      - "8080:8080"  # Monitoring
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
    depends_on:
      - user_service
      - catalog_service
      - reservation_service
      - payment_service
    networks:
      - booklink_network

  # Microservices (unchanged from original)
  user_service:
    build: ./user_service
    container_name: booklink_user
    ports:
      - "5001:5001"
    environment:
      - DB_HOST=user_db
      - DB_NAME=user_service
      - DB_USER=postgres
      - DB_PASSWORD=password
    depends_on:
      - user_db
    networks:
      - booklink_network

  # [... outros serviços ...]

networks:
  booklink_network:
    driver: bridge

volumes:
  user_data:
  catalog_data:
  reservation_data:
  payment_data:
```

## Sistema de Monitoramento

### Scripts de Monitoramento

#### 1. Health Check Script (`health_check_lb.sh`)

```bash
#!/bin/bash

echo "=== BookLink Load Balancer Health Check ==="
echo "Timestamp: $(date)"
echo

# Função para testar endpoint
test_endpoint() {
    local url=$1
    local name=$2
    local response_time=$(curl -o /dev/null -s -w "%{time_total}" "$url" 2>/dev/null)
    local status_code=$(curl -o /dev/null -s -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$status_code" = "200" ]; then
        echo "✅ $name: OK (${response_time}s)"
    else
        echo "❌ $name: FAIL (HTTP $status_code)"
    fi
}

# Testar endpoints
test_endpoint "http://localhost/health" "Load Balancer"
test_endpoint "http://localhost:8080/monitor" "Monitoring"
test_endpoint "http://localhost:8080/nginx_status" "NGINX Stats"

echo
echo "=== Container Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" \
    --filter "name=booklink"

echo
echo "=== NGINX Statistics ==="
curl -s http://localhost:8080/nginx_status 2>/dev/null || echo "Stats not available"
```

#### 2. Monitoring Dashboard (`monitor_lb.sh`)

```bash
#!/bin/bash

# Função para limpar tela
clear_screen() {
    clear
}

# Função para mostrar status
show_status() {
    echo "╔══════════════════════════════════════════════╗"
    echo "║          BookLink Load Balancer Monitor       ║"
    echo "╚══════════════════════════════════════════════╝"
    echo
    echo "📊 Real-time Dashboard - $(date)"
    echo "Press Ctrl+C to exit"
    echo
    
    # Status dos containers
    echo "🐳 Container Status:"
    docker ps --format "{{.Names}}: {{.Status}}" --filter "name=booklink" | \
        sed 's/^/   /'
    echo
    
    # NGINX Statistics
    echo "📈 NGINX Statistics:"
    local stats=$(curl -s http://localhost:8080/nginx_status 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "$stats" | sed 's/^/   /'
    else
        echo "   ❌ Stats not available"
    fi
    echo
    
    # Health checks
    echo "❤️  Health Status:"
    local health=$(curl -s http://localhost/health 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "   ✅ Load Balancer: Healthy"
    else
        echo "   ❌ Load Balancer: Unhealthy"
    fi
    
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Loop principal
while true; do
    clear_screen
    show_status
    sleep 5
done
```

## Como Funciona o Load Balancing

### 1. Roteamento de Requisições

Quando uma requisição chega ao NGINX (porta 80):

1. **Análise da URL**: O NGINX analisa o path da requisição
2. **Seleção do Upstream**: Com base no path, direciona para o serviço correto:
   - `/users/*` → User Service
   - `/books/*` → Catalog Service
   - `/reservations/*` → Reservation Service
   - `/payments/*` → Payment Service

3. **Proxy Headers**: Adiciona headers importantes:
   - `X-Real-IP`: IP real do cliente
   - `X-Forwarded-For`: Chain de proxies
   - `X-Forwarded-Proto`: Protocolo original

### 2. Algoritmo de Balanceamento

- **Algoritmo Atual**: Round-robin (padrão)
- **Funcionamento**: Distribui requisições sequencialmente
- **Vantagens**: Simples e eficaz para cargas similares

### 3. Health Checking

O sistema verifica constantemente:
- **Disponibilidade dos serviços**
- **Tempo de resposta**
- **Status HTTP**
- **Conectividade da rede**

## Monitoramento e Observabilidade

### Endpoints Disponíveis

1. **Aplicação** (porta 80):
   - `http://localhost/users` - Serviço de usuários
   - `http://localhost/books` - Serviço de catálogo
   - `http://localhost/reservations` - Serviço de reservas
   - `http://localhost/payments` - Serviço de pagamentos
   - `http://localhost/health` - Health check do load balancer

2. **Monitoramento** (porta 8080):
   - `http://localhost:8080/monitor` - Dashboard de monitoramento
   - `http://localhost:8080/nginx_status` - Estatísticas do NGINX

### Métricas Disponíveis

As estatísticas do NGINX incluem:
- **Active connections**: Conexões ativas
- **Server accepts**: Total de conexões aceitas
- **Server handled**: Total de conexões processadas
- **Server requests**: Total de requisições
- **Reading/Writing/Waiting**: Estados das conexões

## Comandos Úteis

### Gerenciamento dos Containers

```bash
# Iniciar o sistema
docker-compose -f docker-compose.yml up -d

# Verificar status
docker-compose -f docker-compose.yml ps

# Ver logs do NGINX
docker logs booklink_nginx_lb

# Parar o sistema
docker-compose -f docker-compose.yml down
```

### Monitoramento

```bash
# Health check manual
./health_check_lb.sh

# Dashboard em tempo real
./monitor_lb.sh

# Testar load balancer
curl http://localhost/health
curl http://localhost:8080/nginx_status
```

### Debugging

```bash
# Verificar configuração do NGINX
docker exec booklink_nginx_lb nginx -t

# Reload da configuração
docker exec booklink_nginx_lb nginx -s reload

# Acessar container do NGINX
docker exec -it booklink_nginx_lb sh
```

## Benefícios Implementados

### 1. **Alta Disponibilidade**
- Distribuição de carga entre serviços
- Health checks automáticos
- Failover transparente

### 2. **Performance**
- Balanceamento eficiente
- Conexões keep-alive
- Cache de headers

### 3. **Observabilidade**
- Monitoramento em tempo real
- Métricas detalhadas
- Health checks automáticos

### 4. **Escalabilidade**
- Fácil adição de novas instâncias
- Configuração flexível
- Algoritmos de balanceamento ajustáveis

## Próximos Passos Sugeridos

### Fase 2: Múltiplas Instâncias
- Adicionar réplicas dos serviços
- Configurar health checks avançados
- Implementar algoritmos de balanceamento alternativos

### Fase 3: Monitoramento Avançado
- Integração com Prometheus
- Dashboard com Grafana
- Alertas automáticos

### Fase 4: Segurança
- SSL/TLS termination
- Rate limiting
- Autenticação de requisições

## Troubleshooting

### Problemas Comuns

1. **Container não inicia**:
   ```bash
   docker logs booklink_nginx_lb
   ```

2. **Erro 502 Bad Gateway**:
   - Verificar se os serviços estão rodando
   - Confirmar conectividade de rede

3. **Estatísticas não aparecem**:
   - Verificar se porta 8080 está acessível
   - Confirmar configuração do stub_status

### Logs Importantes

```bash
# Logs do NGINX
docker logs booklink_nginx_lb

# Logs de acesso
docker exec booklink_nginx_lb tail -f /var/log/nginx/access.log

# Logs de erro
docker exec booklink_nginx_lb tail -f /var/log/nginx/error.log
```

---

**Autor**: Sistema BookLink  
**Versão**: 1.0  
**Data**: Janeiro 2026  
**Tecnologias**: NGINX, Docker, Docker Compose, Bash
