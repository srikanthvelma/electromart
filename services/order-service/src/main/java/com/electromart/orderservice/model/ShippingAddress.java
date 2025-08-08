package com.electromart.orderservice.model;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import jakarta.validation.constraints.NotBlank;

@Embeddable
public class ShippingAddress {

    @NotBlank
    @Column(name = "shipping_first_name")
    private String firstName;

    @NotBlank
    @Column(name = "shipping_last_name")
    private String lastName;

    @NotBlank
    @Column(name = "shipping_street")
    private String street;

    @Column(name = "shipping_street2")
    private String street2;

    @NotBlank
    @Column(name = "shipping_city")
    private String city;

    @NotBlank
    @Column(name = "shipping_state")
    private String state;

    @NotBlank
    @Column(name = "shipping_zip_code")
    private String zipCode;

    @NotBlank
    @Column(name = "shipping_country")
    private String country;

    @Column(name = "shipping_phone")
    private String phone;

    @Column(name = "shipping_email")
    private String email;

    // Constructors
    public ShippingAddress() {}

    public ShippingAddress(String firstName, String lastName, String street, String city, 
                          String state, String zipCode, String country) {
        this.firstName = firstName;
        this.lastName = lastName;
        this.street = street;
        this.city = city;
        this.state = state;
        this.zipCode = zipCode;
        this.country = country;
    }

    // Getters and Setters
    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    public String getStreet() {
        return street;
    }

    public void setStreet(String street) {
        this.street = street;
    }

    public String getStreet2() {
        return street2;
    }

    public void setStreet2(String street2) {
        this.street2 = street2;
    }

    public String getCity() {
        return city;
    }

    public void setCity(String city) {
        this.city = city;
    }

    public String getState() {
        return state;
    }

    public void setState(String state) {
        this.state = state;
    }

    public String getZipCode() {
        return zipCode;
    }

    public void setZipCode(String zipCode) {
        this.zipCode = zipCode;
    }

    public String getCountry() {
        return country;
    }

    public void setCountry(String country) {
        this.country = country;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getFullName() {
        return firstName + " " + lastName;
    }

    public String getFullAddress() {
        StringBuilder address = new StringBuilder();
        address.append(street);
        if (street2 != null && !street2.trim().isEmpty()) {
            address.append(", ").append(street2);
        }
        address.append(", ").append(city).append(", ").append(state).append(" ").append(zipCode);
        address.append(", ").append(country);
        return address.toString();
    }
}
