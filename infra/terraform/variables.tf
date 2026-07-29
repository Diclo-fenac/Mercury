variable "do_token" {
  description = "DigitalOcean API Token"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "DigitalOcean Region"
  type        = string
  default     = "nyc3"
}

variable "droplet_size" {
  description = "Size of the Droplet"
  type        = string
  default     = "s-1vcpu-1gb" # The $6/mo instance
}

variable "ssh_key_name" {
  description = "Name of the SSH key already registered in your DigitalOcean account to inject into the Droplet"
  type        = string
}
