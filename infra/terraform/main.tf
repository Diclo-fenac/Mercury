terraform {
  required_version = ">= 1.0.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

# 1. SSH Key setup
data "digitalocean_ssh_key" "admin" {
  name = var.ssh_key_name
}

# 2. Provision the Core Application Node (1vCPU / 1GB or larger)
resource "digitalocean_droplet" "mercury_node" {
  image      = "ubuntu-22-04-x64"
  name       = "mercury-search-prod"
  region     = var.region
  size       = var.droplet_size
  monitoring = true
  ssh_keys   = [data.digitalocean_ssh_key.admin.id]

  # Inject Cloud-Init script to install Docker and prepare the environment
  user_data = file("${path.module}/cloud-init.yaml")

  tags = ["mercury-search", "production"]
}

# 3. Security Firewall
# We strictly block inbound traffic to internal ports (Postgres, Typesense, Redis).
resource "digitalocean_firewall" "mercury_firewall" {
  name = "mercury-production-firewall"

  droplet_ids = [digitalocean_droplet.mercury_node.id]

  # Allow HTTP (80) and HTTPS (443) from anywhere
  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # Allow SSH (22) from anywhere (or restrict to your IP)
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # Allow all outbound traffic (so Docker can pull images, etc.)
  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}
