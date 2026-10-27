package com.kh.back.admin.vehicle;

import java.nio.file.Path;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class VehicleImageConfig implements WebMvcConfigurer {
    private final String location;
    public VehicleImageConfig(@Value("${vehicle-management.image-directory:./uploads/vehicles}") String directory){location=Path.of(directory).toAbsolutePath().normalize().toUri().toString()+"/";}
    @Override public void addResourceHandlers(ResourceHandlerRegistry registry){registry.addResourceHandler("/api/v1/vehicles/images/**").addResourceLocations(location);}
}
