package com.kh.back.admin.vehicle;

import com.kh.back.common.dto.ApiResponse;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/v1/admin/vehicle-images")
public class AdminVehicleImageController {
    private final Path directory;
    public AdminVehicleImageController(@Value("${vehicle-management.image-directory:./uploads/vehicles}") String directory){this.directory=Path.of(directory).toAbsolutePath().normalize();}
    @PostMapping(consumes="multipart/form-data")
    public ResponseEntity<ApiResponse<Map<String,String>>> upload(@RequestParam MultipartFile file) throws IOException {
        if(file.isEmpty()||file.getSize()>5*1024*1024)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"이미지는 5MB 이하여야 합니다.");
        byte[] bytes=file.getBytes();String extension;
        if(bytes.length>12 && bytes[0]==(byte)0x89 && bytes[1]=='P' && bytes[2]=='N' && bytes[3]=='G')extension="png";
        else if(bytes.length>3 && bytes[0]==(byte)0xff && bytes[1]==(byte)0xd8 && bytes[2]==(byte)0xff)extension="jpg";
        else if(bytes.length>12 && new String(bytes,0,4,java.nio.charset.StandardCharsets.US_ASCII).equals("RIFF") && new String(bytes,8,4,java.nio.charset.StandardCharsets.US_ASCII).equals("WEBP"))extension="webp";
        else throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"WebP, PNG, JPG 파일만 업로드할 수 있습니다.");
        if(!extension.equals("webp")){
            try(var input=javax.imageio.ImageIO.createImageInputStream(new java.io.ByteArrayInputStream(bytes))){
                var readers=javax.imageio.ImageIO.getImageReaders(input);
                if(!readers.hasNext())throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"유효한 이미지가 아닙니다.");
                var reader=readers.next();
                try{reader.setInput(input);if(reader.getWidth(0)>10000||reader.getHeight(0)>10000)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"이미지 가로·세로 크기는 10000픽셀 이하여야 합니다.");}
                finally{reader.dispose();}
            }catch(IOException error){throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"손상된 이미지 파일입니다.");}
        }
        String filename=UUID.randomUUID()+"."+extension;Files.createDirectories(directory);
        Files.write(directory.resolve(filename),bytes,java.nio.file.StandardOpenOption.CREATE_NEW);
        String url="/api/v1/vehicles/images/"+filename;
        return ResponseEntity.created(java.net.URI.create(url)).body(ApiResponse.ok(Map.of("url",url)));
    }
}
