<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';

  type SignalMessage = {
  kind: 'offer' | 'answer' | 'candidate';
  data: string;
  };

  let localVideoRef: HTMLVideoElement;
  let remoteVideoRef: HTMLVideoElement;
  let localStream: MediaStream;
  let remoteStream: MediaStream;
  let peerConnection: RTCPeerConnection;
  let ws: WebSocket;
  let roomId = writable<string>('');
  let inCall = writable<Boolean>(false);

  const servers = {
    iceServers: [
      {
        urls: 'stun:stun.l.google.com:19302'
      }
    ]
  };

  async function getRandomRoom() {
  const response = await fetch('http://127.0.0.1:8000/join_random_room');
  const data = await response.json();
  roomId.set(data.room_id);
  return data.room_id;
  }

  onMount(async () => {
    localStream = await navigator.mediaDevices.getUserMedia({
      video: true,
      audio: true
    });
    localVideoRef.srcObject = localStream;
  })

  async function startCall() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.close();
    }

    const roomId = await getRandomRoom();
    ws = new WebSocket(`ws://127.0.0.1:8000/ws/${roomId}`);

    ws.onmessage = handleSignalingMessage;

    try {
      localStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });
      localVideoRef.srcObject = localStream;

      peerConnection = new RTCPeerConnection(servers);
      localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));

      peerConnection.ontrack = (event: RTCTrackEvent) => {
        remoteStream = event.streams[0];
        remoteVideoRef.srcObject = remoteStream;
      };

      peerConnection.onicecandidate = (event: RTCPeerConnectionIceEvent) => {
        if (event.candidate) {
          sendMessage({ kind: 'candidate', data: JSON.stringify(event.candidate) });
        }
      };

      const offer = await peerConnection.createOffer();
      await peerConnection.setLocalDescription(offer);
      sendMessage({ kind: 'offer', data: JSON.stringify(offer) });

      inCall.set(true);
    } catch (error) {
      throw new Error(JSON.stringify(error));
    }
  }

  async function handleSignalingMessage(event: MessageEvent) {
    const message: SignalMessage = await JSON.parse(event.data);

    if (message.kind === 'offer') {
      await peerConnection.setRemoteDescription(new RTCSessionDescription(JSON.parse(message.data)));
      const answer = await peerConnection.createAnswer();
      await peerConnection.setLocalDescription(answer);
      await sendMessage({ kind: 'answer', data: JSON.stringify(answer) });
    } else if (message.kind === 'answer') {
      await peerConnection.setRemoteDescription(new RTCSessionDescription(JSON.parse(message.data)));
    } else if (message.kind === 'candidate') {
      await peerConnection.addIceCandidate(new RTCIceCandidate(JSON.parse(message.data)));
    }
  }

  function sendMessage(message: SignalMessage) {
    if (ws) {
      ws.send(JSON.stringify(message));
    }
  }

  function disconnectCall() {
    if (peerConnection) {
      peerConnection.close();
    }
    if (remoteStream) {
      remoteStream.getTracks().forEach(track => track.stop());
    }
    if (ws) {
      ws.close();
    }

    inCall.set(false);
  }

  function skipCall() {
    disconnectCall();
    startCall();
  }
</script>

<main class="max-h-screen">
    <header class="h-16 p-2 flex items-center">
        <img src="logo.png" alt="" class="h-full">
    </header>
    <div class="grid grid-cols-2 px-2 gap-2">
        <div class="aspect-[4/3] overflow-hidden bg-black/10 rounded">
            <video class="-scale-x-100 w-full " bind:this={remoteVideoRef} autoplay playsinline></video>
        </div>
        <div class="aspect-[4/3] flex items-center justify-center overflow-hidden bg-black/10 rounded">
            <video class="-scale-x-100 w-full " bind:this={localVideoRef} autoplay playsinline muted></video>
        </div>

        <div class="w-full h-full space-y-2">
          {#if !$inCall}
            <button on:click={startCall} class="w-full bg-ogiggle-light disabled:bg-ogiggle-dark font-bold text-gray-50 text-3xl rounded p-2 border-b-8 border-ogiggle-dark disabled:border-ogiggle-light enabled:hover:scale-[98%] duration-200">Start</button>
          {:else}
            <button on:click={skipCall} class="w-full bg-ogiggle-light disabled:bg-ogiggle-dark font-bold text-gray-50 text-3xl rounded p-2 border-b-8 border-ogiggle-dark disabled:border-ogiggle-light enabled:hover:scale-[98%] duration-200">Skip</button>
          {/if}
          <button disabled={!$inCall} on:click={disconnectCall} class="w-full bg-ogiggle-light disabled:bg-ogiggle-dark font-bold text-gray-50 text-3xl rounded p-2 border-b-8 border-ogiggle-dark disabled:border-ogiggle-light enabled:hover:scale-[98%] duration-200">Stop</button>
        </div>
        <div>

        </div>
    </div>
</main>