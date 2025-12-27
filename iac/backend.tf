terraform {
  backend "oci" {
    bucket    = "terraform-state-jacket-server"
    namespace = "lr4bv509x8ke"
    key       = "jacket-server/terraform.tfstate"
    region    = "uk-london-1"
  }
}
