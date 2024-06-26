import cv2
import numpy as np

class Lab4():
    @staticmethod
    def block_method(image1, image2):
        # Load images
        I = cv2.imread(image1)
        J = cv2.imread(image2)

        # Convert images to grayscale
        I_gray = cv2.cvtColor(I, cv2.COLOR_BGR2GRAY)
        J_gray = cv2.cvtColor(J, cv2.COLOR_BGR2GRAY)

        # Calculate absolute difference between images
        abs_diff = cv2.absdiff(I_gray, J_gray)
        cv2.namedWindow('Absolute Difference', cv2.WINDOW_NORMAL)
        cv2.imshow('Absolute Difference', abs_diff)

        # Optical flow parameters
        W2 = 3
        dX = 3
        dY = 3

        # Initialize flow matrices
        u = np.zeros_like(I_gray, dtype=np.float32)
        v = np.zeros_like(I_gray, dtype=np.float32)

        # Iterate over image pixels
        for j in range(W2, I_gray.shape[0] - W2):
            for i in range(W2, I_gray.shape[1] - W2):
                # Extract patch from image I
                IO = np.float32(I_gray[j - W2:j + W2 + 1, i - W2:i + W2 + 1])

                # Search for the most similar patch in image J
                min_distance = float('inf')
                for y in range(-dY, dY + 1):
                    for x in range(-dX, dX + 1):
                        if j + y - W2 >= 0 and j + y + W2 + 1 < J_gray.shape[0] and i + x - W2 >= 0 and i + x + W2 + 1 < J_gray.shape[1]:
                            JO = np.float32(J_gray[j + y - W2:j + y + W2 + 1, i + x - W2:i + x + W2 + 1])
                            distance = np.sqrt(np.sum(np.square(JO - IO)))
                            if distance < min_distance:
                                min_distance = distance
                                u[j, i] = np.uint8(x)
                                v[j, i] = np.uint8(y)

        # Convert flow to polar coordinates
        magnitude, angle = cv2.cartToPolar(u, v)

        # Normalize magnitude to range 0-255
        magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)

        # Convert angle to degrees
        angle_degrees = angle * 90 / np.pi

        # Create HSV image
        hsv = np.zeros((I_gray.shape[0], I_gray.shape[1], 3), dtype=np.uint8)
        hsv[..., 0] = angle_degrees
        hsv[..., 1] = magnitude
        hsv[..., 2] = 255

        # Convert HSV to RGB
        flow_image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        return flow_image

    @staticmethod
    def multiscale_block_method(image1, image2, max_scale=3):
        # Load images
        I = cv2.imread(image1)
        J = cv2.imread(image2)

        # Convert images to grayscale
        I_gray = cv2.cvtColor(I, cv2.COLOR_BGR2GRAY)
        J_gray = cv2.cvtColor(J, cv2.COLOR_BGR2GRAY)

        # Generate image pyramids
        I_pyramid = Lab4.generate_pyramid(I_gray, max_scale)
        J_pyramid = Lab4.generate_pyramid(J_gray, max_scale)

        # Optical flow parameters
        W2 = 3
        dX = 3
        dY = 3

        # Initialize total flow matrices
        u_total = np.zeros_like(I_gray, dtype=np.float32)
        v_total = np.zeros_like(I_gray, dtype=np.float32)

        # Initialize list to store flow images from different scales
        flow_images = []

        # Iterate through scales
        for scale in range(max_scale - 1, -1, -1):
            I_scale = I_pyramid[scale]
            J_scale = J_pyramid[scale]

            # Calculate optical flow for the current scale
            u_scale, v_scale = Lab4.block_method_for_scale(I_scale, J_scale, W2, dX, dY)

            # Propagate flow to the next scale
            if scale > 0:
                u_scale_up = cv2.resize(u_scale, (u_total.shape[1], u_total.shape[0]))
                v_scale_up = cv2.resize(v_scale, (v_total.shape[1], v_total.shape[0]))
                u_total += u_scale_up
                v_total += v_scale_up
            else:
                u_total += u_scale
                v_total += v_scale

            # Convert flow to polar coordinates
            magnitude, angle = cv2.cartToPolar(u_scale, v_scale)

            # Normalize magnitude to range 0-255
            magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)

            # Convert angle to degrees
            angle_degrees = angle * 90 / np.pi

            # Create HSV image
            hsv = np.zeros((I_scale.shape[0], I_scale.shape[1], 3), dtype=np.uint8)
            hsv[..., 0] = angle_degrees
            hsv[..., 1] = magnitude
            hsv[..., 2] = 255

            # Convert HSV to RGB
            flow_image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

            flow_images.append(flow_image)

        # Resize flow images to original size
        original_size_flow_images = []
        for flow_image in flow_images:
            original_size_flow_images.append(cv2.resize(flow_image, (I.shape[1], I.shape[0])))

        return original_size_flow_images

    @staticmethod
    def block_method_for_scale(I, J, W2=3, dY=3, dX=3):
        # Optical flow calculation for a given scale
        # Initialize flow matrices
        u = np.zeros_like(I, dtype=np.float32)
        v = np.zeros_like(I, dtype=np.float32)

        # Iterate over image pixels
        for j in range(W2, I.shape[0] - W2):
            for i in range(W2, I.shape[1] - W2):
                # Extract patch from image I
                IO = np.float32(I[j - W2:j + W2 + 1, i - W2:i + W2 + 1])

                # Search for the most similar patch in image J
                min_distance = float('inf')
                for y in range(-dY, dY + 1):
                    for x in range(-dX, dX + 1):
                        if j + y - W2 >= 0 and j + y + W2 + 1 < J.shape[0] and i + x - W2 >= 0 and i + x + W2 + 1 < J.shape[1]:
                            JO = np.float32(J[j + y - W2:j + y + W2 + 1, i + x - W2:i + x + W2 + 1])
                            distance = np.sqrt(np.sum(np.square(JO - IO)))
                            if distance < min_distance:
                                min_distance = distance
                                u[j, i] = np.uint8(x)
                                v[j, i] = np.uint8(y)

        return u, v

    @staticmethod
    def generate_pyramid(im, max_scale):
        # Generate pyramid of images
        images = [im]
        for k in range(1, max_scale):
            images.append(cv2.resize(images[k-1], (0, 0), fx=0.5, fy=0.5))
        return images

# Usage example
flow_images = Lab4.multiscale_block_method("I.jpg", "J.jpg", max_scale=3)
for idx, image in enumerate(flow_images):
    cv2.imshow(f'Optical Flow Scale {idx}', image)
cv2.waitKey(0)
cv2.destroyAllWindows()
