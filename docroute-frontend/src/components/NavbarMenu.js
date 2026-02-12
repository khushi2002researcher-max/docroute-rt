import { Navbar, Nav, Container, Button } from "react-bootstrap";
import "../styles/Navbar.css";

function NavbarMenu() {
  return (
  <Navbar expand="lg" className="black-navbar">


      <Container>
        <Navbar.Brand href="/">DocRoute-RT</Navbar.Brand>

        <Navbar.Toggle />
        <Navbar.Collapse>
          <Nav className="me-auto">
            <Nav.Link href="/#home">Home</Nav.Link>
            <Nav.Link href="/#features">Features</Nav.Link>
            <Nav.Link href="/#how">How It Works</Nav.Link>
            <Nav.Link href="/about">About</Nav.Link>

          </Nav>

          <Button
  className="custom-nav-btn me-2"
  href="/login"
>
  Login
</Button>

        <Button className="register-btn" href="/register">
  Register
</Button>

        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}

export default NavbarMenu;
