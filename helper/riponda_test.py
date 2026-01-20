import serial
import time

YOUR_COM_PORT = 'COM5'
YOUR_BAUD_RATE = 115200

print(f"Attempting to open port {YOUR_COM_PORT}...")
print("Press the buttons on your Riponda box. Press Ctrl+C to quit.")

try:
    # Open the serial port
    ser = serial.Serial(
        port=YOUR_COM_PORT,
        baudrate=YOUR_BAUD_RATE,
        timeout=0.1
    )
    
    while True:
        if ser.in_waiting > 0:
            raw_bytes = ser.read(ser.in_waiting)
            
            # Print the full byte string
            print(f"\nReceived raw data: {raw_bytes}")
            
            # Print the hex value of each individual byte
            for b in raw_bytes:
                print(f"  -> Byte: {hex(b)}")
        
        time.sleep(0.01)

except serial.SerialException as e:
    print(f"\n--- ERROR ---")
    print(f"Could not open port '{YOUR_COM_PORT}'.")
    print(f"Error details: {e}")
    print("Please check Device Manager and your 'YOUR_COM_PORT' variable.")

except KeyboardInterrupt:
    print("\nQuitting test.")

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print(f"Port {YOUR_COM_PORT} closed.")