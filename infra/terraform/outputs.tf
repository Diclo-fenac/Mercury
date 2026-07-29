output "droplet_ip_address" {
  description = "The public IP address of the Mercury Node"
  value       = digitalocean_droplet.mercury_node.ipv4_address
}

output "ssh_command" {
  description = "Command to SSH into the provisioned node"
  value       = "ssh root@${digitalocean_droplet.mercury_node.ipv4_address}"
}
