using System;
using System.Runtime.InteropServices;

namespace ElevenLabsTTSEngine
{
    /// <summary>
    /// COM interfaces for SAPI5 TTS engine integration.
    /// </summary>

    // ISpTTSEngine interface definition
    [ComImport]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    [Guid("A74D7C8E-4CC5-4F2F-A6EB-804DEE18500E")]
    public interface ISpTTSEngine
    {
        // IUnknown methods (inherited)
        // QueryInterface
        // AddRef
        // Release

        [PreserveSig]
        int Speak(
            [In] uint dwSpeakFlags,
            [In] ref Guid rguidFormatId,
            [In] IntPtr pWaveFormatEx,
            [In] IntPtr pText,
            [In] uint cch,
            [In] IntPtr pTextFragList,
            [Out] out IntPtr ppCoMemChan);

        [PreserveSig]
        int GetOutputFormat(
            [In] ref Guid pTargetFormatId,
            [In] IntPtr pTargetWaveFormatEx,
            [Out] out Guid pDesiredFormatId,
            [Out] out IntPtr ppCoMemDesiredWaveFormatEx);
    }

    // ISpObjectWithToken interface definition
    [ComImport]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    [Guid("5B559F40-E952-11D2-BB91-00C04F8EE6C0")]
    public interface ISpObjectWithToken
    {
        // IUnknown methods (inherited)
        // QueryInterface
        // AddRef
        // Release

        [PreserveSig]
        int SetObjectToken([In] IntPtr pToken);

        [PreserveSig]
        int GetObjectToken([Out] out IntPtr ppToken);
    }

    /// <summary>
    /// WAVEFORMATEX structure for audio format specification.
    /// </summary>
    [StructLayout(LayoutKind.Sequential)]
    public struct WAVEFORMATEX
    {
        public ushort wFormatTag;
        public ushort nChannels;
        public uint nSamplesPerSec;
        public uint nAvgBytesPerSec;
        public ushort nBlockAlign;
        public ushort wBitsPerSample;
        public ushort cbSize;
    }
}
